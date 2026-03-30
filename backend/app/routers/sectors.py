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
        {"source": "greenhouse", "slug": "gusto"},
        {"source": "greenhouse", "slug": "carta"},
        {"source": "greenhouse", "slug": "mercury"},
    ],
    "AI / ML": [
        # Most major AI labs (OpenAI, Cohere, HuggingFace) use their own ATS
        {"source": "greenhouse", "slug": "anthropic"},
        {"source": "greenhouse", "slug": "databricks"},
    ],
    "Dev Tools": [
        {"source": "greenhouse", "slug": "vercel"},
        {"source": "greenhouse", "slug": "datadog"},
        {"source": "greenhouse", "slug": "postman"},
        {"source": "greenhouse", "slug": "cloudflare"},
        {"source": "greenhouse", "slug": "circleci"},
    ],
    "Consumer": [
        {"source": "greenhouse", "slug": "airbnb"},
        {"source": "greenhouse", "slug": "instacart"},
        {"source": "greenhouse", "slug": "duolingo"},
        {"source": "greenhouse", "slug": "reddit"},
        {"source": "greenhouse", "slug": "lyft"},
        {"source": "greenhouse", "slug": "pinterest"},
        {"source": "greenhouse", "slug": "discord"},
    ],
    "Enterprise / Cloud": [
        {"source": "greenhouse", "slug": "figma"},
        {"source": "greenhouse", "slug": "airtable"},
        {"source": "greenhouse", "slug": "twilio"},
        {"source": "greenhouse", "slug": "intercom"},
    ],
    "Crypto / Web3": [
        {"source": "greenhouse", "slug": "coinbase"},
        {"source": "greenhouse", "slug": "alchemy"},
        {"source": "greenhouse", "slug": "fireblocks"},
    ],
    "Healthcare": [
        {"source": "greenhouse", "slug": "oscar"},
        {"source": "greenhouse", "slug": "tripactions"},  # Navan
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

    MAX_COMPANIES = 40
    current = (await db.execute(
        select(SessionCompany).where(SessionCompany.session_id == x_session_id)
    )).scalars().all()
    current_slugs = {(sc.source, sc.slug) for sc in current}

    remaining = [c for c in companies if (c["source"], c["slug"]) not in current_slugs]

    if len(current) + len(remaining) > MAX_COMPANIES:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Adding this sector would exceed the {MAX_COMPANIES}-company limit.",
        )

    for c in remaining:
        slug, source = c["slug"], c["source"]
        cs = (await db.execute(
            select(CompanySource).where(
                CompanySource.source == source, CompanySource.slug == slug
            )
        )).scalar_one_or_none()
        if not cs:
            db.add(CompanySource(source=source, slug=slug))
        db.add(SessionCompany(session_id=x_session_id, source=source, slug=slug))

    await db.commit()
    return {"added": len(remaining)}
