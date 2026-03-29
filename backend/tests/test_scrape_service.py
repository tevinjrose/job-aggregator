"""Unit tests for run_scrape — uses mocked scrapers to avoid real HTTP calls."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from tests.conftest import SESSION_ID

from app.models import CompanySource, SessionCompany
from app.services.scrape_service import run_scrape


def _make_job(slug: str, source: str = "greenhouse", location: str = "San Francisco, CA") -> dict:
    return {
        "external_id": f"{source}:{slug}:job-1",
        "source": source,
        "company_slug": slug,
        "title": "Software Engineer",
        "location": location,
        "salary": None,
        "apply_url": f"https://example.com/jobs/1",
        "description": "A great job.",
        "posted_at": datetime.now(timezone.utc),
    }


async def _seed_company(db, session_id: str, source: str, slug: str, cached: bool = False):
    sc = SessionCompany(session_id=session_id, source=source, slug=slug)
    db.add(sc)
    cs = CompanySource(source=source, slug=slug)
    if cached:
        # Set last_scraped_at to 1 hour ago (within the 6-hour cache window)
        cs.last_scraped_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.add(cs)
    await db.commit()


# ── No companies ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_no_companies(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        result = await run_scrape(db, SESSION_ID)
    assert result == {"total_fetched": 0, "new_jobs": 0, "cached": 0, "no_results": []}


# ── New jobs found ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_new_jobs(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "stripe")

    with patch(
        "app.services.scrape_service.GreenhouseScraper.fetch_jobs",
        new=AsyncMock(return_value=[_make_job("stripe")]),
    ):
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    assert result["new_jobs"] == 1
    assert result["total_fetched"] == 1
    assert result["cached"] == 0
    assert result["no_results"] == []


# ── Duplicate jobs not double-counted ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_no_duplicate_jobs(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "stripe")

    job = _make_job("stripe")
    with patch(
        "app.services.scrape_service.GreenhouseScraper.fetch_jobs",
        new=AsyncMock(return_value=[job]),
    ):
        async with TestSession() as db:
            await run_scrape(db, SESSION_ID)

        # Run again — same job should not be re-added
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    assert result["new_jobs"] == 0


# ── Company returning no listings → no_results ────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_no_results_for_slug(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "meta")

    with patch(
        "app.services.scrape_service.GreenhouseScraper.fetch_jobs",
        new=AsyncMock(return_value=[]),  # meta returns nothing
    ):
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    assert result["new_jobs"] == 0
    assert result["total_fetched"] == 0
    assert "meta" in result["no_results"]


# ── Cached company skipped ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_cached_company_skipped(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "stripe", cached=True)

    mock_fetch = AsyncMock(return_value=[_make_job("stripe")])
    with patch("app.services.scrape_service.GreenhouseScraper.fetch_jobs", new=mock_fetch):
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    # Should not have called the scraper
    mock_fetch.assert_not_called()
    assert result["cached"] == 1
    assert result["new_jobs"] == 0
    assert result["no_results"] == []


# ── Mixed: one good slug, one empty slug ──────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_mixed_results(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "stripe")
        await _seed_company(db, SESSION_ID, "greenhouse", "meta")

    def fake_fetch(slugs):
        # stripe returns a job, meta returns nothing
        jobs = [_make_job("stripe")] if "stripe" in slugs else []
        return jobs

    with patch(
        "app.services.scrape_service.GreenhouseScraper.fetch_jobs",
        new=AsyncMock(side_effect=fake_fetch),
    ):
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    assert result["new_jobs"] == 1
    assert "meta" in result["no_results"]
    assert "stripe" not in result["no_results"]


# ── Non-US jobs are filtered out ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scrape_non_us_jobs_excluded(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        await _seed_company(db, SESSION_ID, "greenhouse", "stripe")

    non_us_job = _make_job("stripe", location="London, UK")
    with patch(
        "app.services.scrape_service.GreenhouseScraper.fetch_jobs",
        new=AsyncMock(return_value=[non_us_job]),
    ):
        async with TestSession() as db:
            result = await run_scrape(db, SESSION_ID)

    assert result["new_jobs"] == 0
    assert result["total_fetched"] == 0
    # no_results only tracks slugs with zero API results — stripe returned a job
    # from the API (just non-US), so it is NOT in no_results
    assert "stripe" not in result["no_results"]
