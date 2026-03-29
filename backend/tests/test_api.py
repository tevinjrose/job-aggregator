"""Integration tests for API endpoints."""
import pytest
import pytest_asyncio
from tests.conftest import SESSION_ID

HEADERS = {"X-Session-ID": SESSION_ID}


# ── Criteria ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_criteria_empty(client):
    r = await client.get("/api/settings/criteria", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["titles"] == []
    assert data["keywords"] == []
    assert data["locations"] == []


@pytest.mark.asyncio
async def test_save_and_get_criteria(client):
    payload = {
        "titles": ["Software Engineer", "Backend Engineer"],
        "keywords": ["Python", "FastAPI"],
        "locations": ["New York", "Remote"],
        "min_salary": 120000,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": True,
    }
    r = await client.put("/api/settings/criteria", json=payload, headers=HEADERS)
    assert r.status_code == 200

    r = await client.get("/api/settings/criteria", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["titles"] == ["Software Engineer", "Backend Engineer"]
    assert data["min_salary"] == 120000


@pytest.mark.asyncio
async def test_criteria_is_session_isolated(client):
    payload = {
        "titles": ["Data Scientist"],
        "keywords": [],
        "locations": [],
        "min_salary": None,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": False,
    }
    await client.put("/api/settings/criteria", json=payload, headers=HEADERS)

    # Different session should get empty defaults
    r = await client.get(
        "/api/settings/criteria", headers={"X-Session-ID": "other-session-xyz"}
    )
    assert r.json()["titles"] == []


# ── Companies ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_company(client):
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    assert r.status_code == 201
    assert r.json()["slug"] == "stripe"


@pytest.mark.asyncio
async def test_add_duplicate_company_rejected(client):
    await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_company_cap_at_20(client):
    for i in range(20):
        r = await client.post(
            "/api/settings/companies",
            json={"source": "greenhouse", "slug": f"company-{i}"},
            headers=HEADERS,
        )
        assert r.status_code == 201

    # 21st should be rejected
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "company-overflow"},
        headers=HEADERS,
    )
    assert r.status_code == 400
    assert "Maximum" in r.json()["detail"]


@pytest.mark.asyncio
async def test_delete_company(client):
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    company_id = r.json()["id"]

    r = await client.delete(f"/api/settings/companies/{company_id}", headers=HEADERS)
    assert r.status_code == 204

    r = await client.get("/api/settings/companies", headers=HEADERS)
    assert r.json() == []


@pytest.mark.asyncio
async def test_delete_other_sessions_company_rejected(client):
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    company_id = r.json()["id"]

    r = await client.delete(
        f"/api/settings/companies/{company_id}",
        headers={"X-Session-ID": "attacker-session"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_companies_are_session_isolated(client):
    await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )

    r = await client.get(
        "/api/settings/companies", headers={"X-Session-ID": "other-session"}
    )
    assert r.json() == []


# ── Jobs feed ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_empty_feed_no_companies(client):
    r = await client.get("/api/jobs?tab=feed", headers=HEADERS)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_feed_tabs_exist(client):
    for tab in ["feed", "saved", "applied"]:
        r = await client.get(f"/api/jobs?tab={tab}", headers=HEADERS)
        assert r.status_code == 200


# ── Scrape cooldown ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scrape_cooldown_enforced(client):
    # Patch last scrape time to simulate a recent scrape
    from app.routers.scraper import _last_scrape
    import time
    _last_scrape[SESSION_ID] = time.time()

    r = await client.post("/api/scraper/run", headers=HEADERS)
    assert r.status_code == 429
    assert "wait" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scrape_allowed_after_cooldown(client):
    from app.routers.scraper import _last_scrape
    import time
    # Simulate scrape from 10 minutes ago
    _last_scrape[SESSION_ID] = time.time() - 600

    r = await client.post("/api/scraper/run", headers=HEADERS)
    # No companies added so it'll return empty result, but not 429
    assert r.status_code == 200


# ── Scraper status ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scraper_status_idle(client):
    r = await client.get("/api/scraper/status", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "idle"


# ── Sectors ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_sectors(client):
    r = await client.get("/api/sectors", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "Fintech" in data
    assert "AI / ML" in data
    assert len(data["Fintech"]) > 0


@pytest.mark.asyncio
async def test_add_sector(client):
    r = await client.post(
        "/api/sectors/add", params={"sector_name": "Fintech"}, headers=HEADERS
    )
    assert r.status_code == 200
    assert r.json()["added"] > 0

    # Companies should now appear in session
    r = await client.get("/api/settings/companies", headers=HEADERS)
    slugs = [c["slug"] for c in r.json()]
    assert "stripe" in slugs


@pytest.mark.asyncio
async def test_remove_sector(client):
    # Add first
    await client.post(
        "/api/sectors/add", params={"sector_name": "Fintech"}, headers=HEADERS
    )
    # Remove
    r = await client.delete(
        "/api/sectors", params={"sector_name": "Fintech"}, headers=HEADERS
    )
    assert r.status_code == 200
    assert r.json()["removed"] > 0

    r = await client.get("/api/settings/companies", headers=HEADERS)
    slugs = [c["slug"] for c in r.json()]
    assert "stripe" not in slugs


@pytest.mark.asyncio
async def test_add_invalid_sector(client):
    r = await client.post(
        "/api/sectors/add", params={"sector_name": "NotASector"}, headers=HEADERS
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_sector_respects_company_cap(client):
    # Fill up to 19 companies manually
    for i in range(19):
        await client.post(
            "/api/settings/companies",
            json={"source": "greenhouse", "slug": f"filler-{i}"},
            headers=HEADERS,
        )

    # Adding a sector with 6 companies should only add 1 (up to cap of 20)
    r = await client.post(
        "/api/sectors/add", params={"sector_name": "Fintech"}, headers=HEADERS
    )
    assert r.status_code == 200
    assert r.json()["added"] == 1
