from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CompanySource, Job, SessionCompany
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.services.filters import is_us_location

CACHE_HOURS = 6  # skip re-scraping a company within this window


async def run_scrape(db: AsyncSession, session_id: str) -> dict:
    companies = (
        await db.execute(
            select(SessionCompany).where(SessionCompany.session_id == session_id)
        )
    ).scalars().all()

    if not companies:
        return {"total_fetched": 0, "new_jobs": 0, "cached": 0, "scored": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_HOURS)

    greenhouse_slugs, lever_slugs = [], []
    cached_count = 0

    for sc in companies:
        cs = (
            await db.execute(
                select(CompanySource).where(
                    CompanySource.source == sc.source,
                    CompanySource.slug == sc.slug,
                )
            )
        ).scalar_one_or_none()

        last = cs.last_scraped_at if cs else None
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)

        if last and last > cutoff:
            cached_count += 1
            continue

        if sc.source == "greenhouse":
            greenhouse_slugs.append(sc.slug)
        else:
            lever_slugs.append(sc.slug)

    all_jobs: list[dict] = []
    if greenhouse_slugs:
        all_jobs.extend(await GreenhouseScraper().fetch_jobs(greenhouse_slugs))
    if lever_slugs:
        all_jobs.extend(await LeverScraper().fetch_jobs(lever_slugs))

    us_jobs = [j for j in all_jobs if is_us_location(j.get("location"))]
    skipped = len(all_jobs) - len(us_jobs)
    print(f"[Scrape] {len(all_jobs)} fetched, {skipped} non-US skipped, {len(us_jobs)} to save")

    new_count = 0
    for job_data in us_jobs:
        exists = (
            await db.execute(
                select(Job).where(Job.external_id == job_data["external_id"])
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(Job(**job_data))
            new_count += 1

    # Update last_scraped_at for freshly scraped slugs
    now = datetime.now(timezone.utc)
    for source, slugs in [("greenhouse", greenhouse_slugs), ("lever", lever_slugs)]:
        for slug in slugs:
            cs = (
                await db.execute(
                    select(CompanySource).where(
                        CompanySource.source == source, CompanySource.slug == slug
                    )
                )
            ).scalar_one_or_none()
            if cs:
                cs.last_scraped_at = now

    await db.commit()

    return {
        "total_fetched": len(us_jobs),
        "new_jobs": new_count,
        "cached": cached_count,
    }
