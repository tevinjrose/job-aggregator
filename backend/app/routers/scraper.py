import time

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.services.scrape_service import run_scrape
from app.services.scoring import score_unscored_jobs, scoring_progress

router = APIRouter()

SCRAPE_COOLDOWN_SECONDS = 300  # 5 minutes
_last_scrape: dict[str, float] = {}  # session_id -> timestamp


async def _background_score(session_id: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            scored = await score_unscored_jobs(db, session_id)
            print(f"[Background] Scored {scored} jobs for session {session_id[:8]}")
        except Exception as exc:
            print(f"[Background] Scoring failed: {exc}")


@router.post("/run")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    now = time.time()
    last = _last_scrape.get(x_session_id, 0)
    wait = SCRAPE_COOLDOWN_SECONDS - (now - last)
    if wait > 0:
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {int(wait)} seconds before scraping again."
        )

    _last_scrape[x_session_id] = now
    scoring_progress.pop(x_session_id, None)
    result = await run_scrape(db, x_session_id)
    background_tasks.add_task(_background_score, x_session_id)
    return result


@router.get("/status")
async def scrape_status(x_session_id: str = Header(...)):
    progress = scoring_progress.get(x_session_id)
    if not progress:
        return {"status": "idle"}
    if progress["done"]:
        return {"status": "done", "scored": progress["scored"], "total": progress["total"]}
    return {"status": "scoring", "scored": progress["scored"], "total": progress["total"]}
