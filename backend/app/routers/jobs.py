import json
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job, JobScore, JobStatus, SessionCompany, SessionCriteria
from app.schemas import JobOut, JobStatusUpdate
from app.services.filters import is_us_location, title_matches

router = APIRouter()


def _preferred_location_ok(location: str, preferred: list[str]) -> bool:
    """Secondary filter: match user's preferred cities/regions (within US)."""
    if not preferred:
        return True
    loc = location.lower() if location else ""
    return any(p.lower() in loc for p in preferred)


def _build_job_out(job: Job, scores: dict, statuses: dict) -> JobOut:
    return JobOut(
        id=job.id,
        external_id=job.external_id,
        source=job.source,
        company_slug=job.company_slug,
        title=job.title,
        location=job.location,
        salary=job.salary,
        apply_url=job.apply_url,
        posted_at=job.posted_at,
        score=scores.get(job.id),
        status=statuses.get(job.id),
    )


@router.get("", response_model=list[JobOut])
async def list_jobs(
    tab: Literal["feed", "saved", "applied"] = Query(default="feed"),
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    session_id = x_session_id

    companies = (
        await db.execute(
            select(SessionCompany).where(SessionCompany.session_id == session_id)
        )
    ).scalars().all()

    if not companies:
        return []

    slug_filters = [
        (Job.source == sc.source) & (Job.company_slug == sc.slug) for sc in companies
    ]

    jobs = (
        await db.execute(select(Job).where(or_(*slug_filters)))
    ).scalars().all()

    scores = {
        r.job_id: r.score
        for r in (
            await db.execute(
                select(JobScore).where(JobScore.session_id == session_id)
            )
        ).scalars().all()
    }

    statuses = {
        r.job_id: r.status
        for r in (
            await db.execute(
                select(JobStatus).where(JobStatus.session_id == session_id)
            )
        ).scalars().all()
    }

    if tab == "saved":
        filtered = [j for j in jobs if statuses.get(j.id) == "saved"]
    elif tab == "applied":
        filtered = [j for j in jobs if statuses.get(j.id) == "applied"]
    else:
        # Feed: exclude actioned jobs, then apply criteria pre-filter
        actioned = {"saved", "applied", "dismissed"}
        filtered = [j for j in jobs if statuses.get(j.id) not in actioned]

        criteria = (
            await db.execute(
                select(SessionCriteria).where(SessionCriteria.session_id == session_id)
            )
        ).scalar_one_or_none()

        if criteria:
            preferred_locs = json.loads(criteria.locations)
            desired_titles = json.loads(criteria.titles)
            excluded = [c.lower() for c in json.loads(criteria.excluded_companies)]
            filtered = [
                j for j in filtered
                if is_us_location(j.location)
                and title_matches(j.title, desired_titles)
                and _preferred_location_ok(j.location, preferred_locs)
                and j.company_slug.lower() not in excluded
            ]

    result = [_build_job_out(j, scores, statuses) for j in filtered]
    result.sort(
        key=lambda j: (j.score if j.score is not None else -1, j.posted_at.timestamp()),
        reverse=True,
    )
    return result


@router.patch("/{job_id}/status", response_model=JobOut)
async def update_job_status(
    job_id: int,
    body: JobStatusUpdate,
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    session_id = x_session_id

    job = (
        await db.execute(select(Job).where(Job.id == job_id))
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    existing = (
        await db.execute(
            select(JobStatus).where(
                JobStatus.session_id == session_id, JobStatus.job_id == job_id
            )
        )
    ).scalar_one_or_none()

    if body.status is None:
        if existing:
            await db.delete(existing)
    elif existing:
        existing.status = body.status
    else:
        db.add(JobStatus(session_id=session_id, job_id=job_id, status=body.status))

    await db.commit()

    score_row = (
        await db.execute(
            select(JobScore).where(
                JobScore.session_id == session_id, JobScore.job_id == job_id
            )
        )
    ).scalar_one_or_none()

    return JobOut(
        id=job.id,
        external_id=job.external_id,
        source=job.source,
        company_slug=job.company_slug,
        title=job.title,
        location=job.location,
        salary=job.salary,
        apply_url=job.apply_url,
        posted_at=job.posted_at,
        score=score_row.score if score_row else None,
        status=body.status,
    )
