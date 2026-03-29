"""Performance tests — response time and concurrency checks."""
import asyncio
import time
import pytest
from tests.conftest import SESSION_ID

HEADERS = {"X-Session-ID": SESSION_ID}

# Thresholds (seconds) — generous for in-process test client
FAST = 0.1    # simple reads
MEDIUM = 0.5  # writes / small queries
BULK = 2.0    # 20 concurrent requests


# ── Individual endpoint latency ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criteria_get_is_fast(client):
    start = time.perf_counter()
    r = await client.get("/api/settings/criteria", headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < FAST, f"GET /criteria took {elapsed:.3f}s — expected < {FAST}s"


@pytest.mark.asyncio
async def test_criteria_save_is_fast(client):
    payload = {
        "titles": ["Software Engineer"],
        "keywords": ["Python"],
        "locations": ["Remote"],
        "min_salary": 120000,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": False,
    }
    start = time.perf_counter()
    r = await client.put("/api/settings/criteria", json=payload, headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < MEDIUM, f"PUT /criteria took {elapsed:.3f}s — expected < {MEDIUM}s"


@pytest.mark.asyncio
async def test_jobs_feed_is_fast(client):
    start = time.perf_counter()
    r = await client.get("/api/jobs?tab=feed", headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < FAST, f"GET /jobs took {elapsed:.3f}s — expected < {FAST}s"


@pytest.mark.asyncio
async def test_companies_list_is_fast(client):
    start = time.perf_counter()
    r = await client.get("/api/settings/companies", headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < FAST, f"GET /companies took {elapsed:.3f}s — expected < {FAST}s"


@pytest.mark.asyncio
async def test_scraper_status_is_fast(client):
    start = time.perf_counter()
    r = await client.get("/api/scraper/status", headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < FAST, f"GET /scraper/status took {elapsed:.3f}s — expected < {FAST}s"


@pytest.mark.asyncio
async def test_sectors_list_is_fast(client):
    start = time.perf_counter()
    r = await client.get("/api/sectors", headers=HEADERS)
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < FAST, f"GET /sectors took {elapsed:.3f}s — expected < {FAST}s"


# ── Bulk operations ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_adding_20_companies_completes_in_time(client):
    """Adding the maximum 20 companies should complete well within 2 seconds."""
    start = time.perf_counter()
    for i in range(20):
        r = await client.post(
            "/api/settings/companies",
            json={"source": "greenhouse", "slug": f"perf-company-{i}"},
            headers=HEADERS,
        )
        assert r.status_code == 201
    elapsed = time.perf_counter() - start
    assert elapsed < BULK, f"Adding 20 companies took {elapsed:.3f}s — expected < {BULK}s"


@pytest.mark.asyncio
async def test_sector_add_completes_in_time(client):
    """Bulk-adding a full sector should complete within 1 second."""
    start = time.perf_counter()
    r = await client.post(
        "/api/sectors/add", params={"sector_name": "Fintech"}, headers=HEADERS
    )
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 1.0, f"Sector add took {elapsed:.3f}s — expected < 1.0s"


# ── Concurrency ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concurrent_criteria_reads(client):
    """10 simultaneous GET /criteria requests should all succeed without errors."""
    tasks = [
        client.get("/api/settings/criteria", headers={"X-Session-ID": f"session-{i}"})
        for i in range(10)
    ]
    start = time.perf_counter()
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    for r in responses:
        assert r.status_code == 200
    assert elapsed < BULK, f"10 concurrent reads took {elapsed:.3f}s — expected < {BULK}s"


@pytest.mark.asyncio
async def test_concurrent_criteria_writes_no_cross_contamination(client):
    """10 sessions writing different titles concurrently should stay isolated."""
    async def write_and_read(session_id: str, title: str):
        headers = {"X-Session-ID": session_id}
        await client.put(
            "/api/settings/criteria",
            json={
                "titles": [title],
                "keywords": [],
                "locations": [],
                "min_salary": None,
                "excluded_companies": [],
                "exclude_onsite_outside_major_cities": False,
            },
            headers=headers,
        )
        r = await client.get("/api/settings/criteria", headers=headers)
        return r.json()["titles"]

    tasks = [
        write_and_read(f"concurrent-session-{i}", f"UniqueTitle-{i}")
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)

    for i, titles in enumerate(results):
        assert titles == [f"UniqueTitle-{i}"], (
            f"Session {i} got wrong titles: {titles}"
        )


@pytest.mark.asyncio
async def test_concurrent_company_adds_respect_cap(client):
    """20 concurrent add requests from the same session should not exceed the cap."""
    tasks = [
        client.post(
            "/api/settings/companies",
            json={"source": "greenhouse", "slug": f"concurrent-co-{i}"},
            headers=HEADERS,
        )
        for i in range(25)
    ]
    responses = await asyncio.gather(*tasks)

    success = sum(1 for r in responses if r.status_code == 201)
    rejected = sum(1 for r in responses if r.status_code in (400, 409))

    # No more than 20 should succeed; the rest should be cleanly rejected
    assert success <= 20
    assert success + rejected == 25
