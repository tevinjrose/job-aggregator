from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CompanySource, SessionCompany

router = APIRouter()

SECTORS: dict[str, list[dict]] = {
    "Fintech": [
        {"source": "greenhouse", "slug": "stripe"},
        {"source": "greenhouse", "slug": "brex"},
        {"source": "greenhouse", "slug": "chime"},
        {"source": "lever", "slug": "plaid"},
        {"source": "greenhouse", "slug": "robinhood"},
        {"source": "greenhouse", "slug": "affirm"},
    ],
    "AI / ML": [
        {"source": "greenhouse", "slug": "openai"},
        {"source": "greenhouse", "slug": "anthropic"},
        {"source": "greenhouse", "slug": "cohere"},
        {"source": "lever", "slug": "scale-ai"},
        {"source": "greenhouse", "slug": "huggingface"},
        {"source": "greenhouse", "slug": "mistral"},
    ],
    "Dev Tools": [
        {"source": "greenhouse", "slug": "vercel"},
        {"source": "greenhouse", "slug": "hashicorp"},
        {"source": "greenhouse", "slug": "datadog"},
        {"source": "greenhouse", "slug": "circleci"},
        {"source": "lever", "slug": "netlify"},
        {"source": "greenhouse", "slug": "linear"},
    ],
    "Consumer": [
        {"source": "greenhouse", "slug": "airbnb"},
        {"source": "greenhouse", "slug": "doordash"},
        {"source": "greenhouse", "slug": "instacart"},
        {"source": "greenhouse", "slug": "duolingo"},
        {"source": "greenhouse", "slug": "reddit"},
    ],
    "Enterprise / Cloud": [
        {"source": "greenhouse", "slug": "snowflake"},
        {"source": "greenhouse", "slug": "databricks"},
        {"source": "greenhouse", "slug": "notion"},
        {"source": "greenhouse", "slug": "figma"},
        {"source": "greenhouse", "slug": "airtable"},
    ],
    "Crypto / Web3": [
        {"source": "greenhouse", "slug": "coinbase"},
        {"source": "lever", "slug": "chainalysis"},
        {"source": "greenhouse", "slug": "polygon"},
        {"source": "greenhouse", "slug": "alchemy"},
    ],
    "Healthcare": [
        {"source": "greenhouse", "slug": "oscar"},
        {"source": "greenhouse", "slug": "ro"},
        {"source": "lever", "slug": "tempus"},
        {"source": "greenhouse", "slug": "hims"},
    ],
}


@router.get("")
async def list_sectors():
    return {
        sector: [{"source": c["source"], "slug": c["slug"]} for c in companies]
        for sector, companies in SECTORS.items()
    }


@router.delete("")
async def remove_sector(
    sector_name: str,
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    companies = SECTORS.get(sector_name)
    if not companies:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sector not found.")

    removed = 0
    for c in companies:
        sc = (await db.execute(
            select(SessionCompany).where(
                SessionCompany.session_id == x_session_id,
                SessionCompany.source == c["source"],
                SessionCompany.slug == c["slug"],
            )
        )).scalar_one_or_none()
        if sc:
            await db.delete(sc)
            removed += 1

    await db.commit()
    return {"removed": removed}


@router.post("/add")
async def add_sector(
    sector_name: str,
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    companies = SECTORS.get(sector_name)
    if not companies:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sector not found.")

    MAX_COMPANIES = 20
    current_count = len((await db.execute(
        select(SessionCompany).where(SessionCompany.session_id == x_session_id)
    )).scalars().all())

    added = 0
    for c in companies:
        if current_count + added >= MAX_COMPANIES:
            break
        slug = c["slug"]
        source = c["source"]

        existing = (await db.execute(
            select(SessionCompany).where(
                SessionCompany.session_id == x_session_id,
                SessionCompany.source == source,
                SessionCompany.slug == slug,
            )
        )).scalar_one_or_none()
        if existing:
            continue

        cs = (await db.execute(
            select(CompanySource).where(
                CompanySource.source == source, CompanySource.slug == slug
            )
        )).scalar_one_or_none()
        if not cs:
            db.add(CompanySource(source=source, slug=slug))

        db.add(SessionCompany(session_id=x_session_id, source=source, slug=slug))
        added += 1

    await db.commit()
    return {"added": added}
