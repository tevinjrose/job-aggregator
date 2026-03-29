import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CompanySource, SessionCompany, SessionCriteria
from app.schemas import (
    SessionCompanyCreate,
    SessionCompanyOut,
    UserCriteriaIn,
    UserCriteriaOut,
)

router = APIRouter()


def session_id_header(x_session_id: str = Header(...)) -> str:
    return x_session_id


# ── Criteria ───────────────────────────────────────────────────────────────────

@router.get("/criteria", response_model=UserCriteriaOut)
async def get_criteria(
    session_id: str = Depends(session_id_header),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionCriteria).where(SessionCriteria.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return UserCriteriaOut()  # empty defaults for new sessions
    return UserCriteriaOut(
        titles=json.loads(row.titles),
        keywords=json.loads(row.keywords),
        locations=json.loads(row.locations),
        min_salary=row.min_salary,
        excluded_companies=json.loads(row.excluded_companies),
        exclude_onsite_outside_major_cities=row.exclude_onsite_outside_major_cities,
    )


@router.put("/criteria", response_model=UserCriteriaOut)
async def save_criteria(
    body: UserCriteriaIn,
    session_id: str = Depends(session_id_header),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionCriteria).where(SessionCriteria.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = SessionCriteria(session_id=session_id)
        db.add(row)

    row.titles = json.dumps(body.titles)
    row.keywords = json.dumps(body.keywords)
    row.locations = json.dumps(body.locations)
    row.min_salary = body.min_salary
    row.excluded_companies = json.dumps(body.excluded_companies)
    row.exclude_onsite_outside_major_cities = body.exclude_onsite_outside_major_cities

    await db.commit()
    return body


# ── Companies ──────────────────────────────────────────────────────────────────

@router.get("/companies", response_model=list[SessionCompanyOut])
async def list_companies(
    session_id: str = Depends(session_id_header),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionCompany, CompanySource.last_scraped_at)
        .join(
            CompanySource,
            (CompanySource.source == SessionCompany.source)
            & (CompanySource.slug == SessionCompany.slug),
            isouter=True,
        )
        .where(SessionCompany.session_id == session_id)
        .order_by(SessionCompany.source, SessionCompany.slug)
    )
    return [
        SessionCompanyOut(id=sc.id, source=sc.source, slug=sc.slug, last_scraped_at=last)
        for sc, last in result.all()
    ]


@router.post("/companies", response_model=SessionCompanyOut, status_code=201)
async def add_company(
    body: SessionCompanyCreate,
    session_id: str = Depends(session_id_header),
    db: AsyncSession = Depends(get_db),
):
    MAX_COMPANIES = 20
    slug = body.slug.strip().lower()

    count = len((await db.execute(
        select(SessionCompany).where(SessionCompany.session_id == session_id)
    )).scalars().all())
    if count >= MAX_COMPANIES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {MAX_COMPANIES} companies per session."
        )

    existing = await db.execute(
        select(SessionCompany).where(
            SessionCompany.session_id == session_id,
            SessionCompany.source == body.source,
            SessionCompany.slug == slug,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already in your list.")

    # Ensure global CompanySource entry exists (for cache tracking)
    cs = await db.execute(
        select(CompanySource).where(
            CompanySource.source == body.source, CompanySource.slug == slug
        )
    )
    if not cs.scalar_one_or_none():
        db.add(CompanySource(source=body.source, slug=slug))

    sc = SessionCompany(session_id=session_id, source=body.source, slug=slug)
    db.add(sc)
    await db.commit()
    await db.refresh(sc)

    return SessionCompanyOut(id=sc.id, source=sc.source, slug=sc.slug, last_scraped_at=None)


@router.delete("/companies/{company_id}", status_code=204)
async def remove_company(
    company_id: int,
    session_id: str = Depends(session_id_header),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionCompany).where(
            SessionCompany.id == company_id,
            SessionCompany.session_id == session_id,
        )
    )
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Not found.")
    await db.delete(sc)
    await db.commit()
