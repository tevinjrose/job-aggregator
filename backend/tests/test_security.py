"""Security tests — input validation, session isolation, and injection hardening."""
import pytest
from tests.conftest import SESSION_ID

HEADERS = {"X-Session-ID": SESSION_ID}


# ── Missing / malformed session header ────────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_session_header_criteria(client):
    """Requests without X-Session-ID should be rejected with 422."""
    r = await client.get("/api/settings/criteria")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_missing_session_header_companies(client):
    r = await client.get("/api/settings/companies")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_missing_session_header_jobs(client):
    r = await client.get("/api/jobs")
    assert r.status_code == 422


# ── SQL injection in slug field ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sql_injection_in_slug(client):
    """SQL injection attempt in slug should not crash the server."""
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "'; DROP TABLE jobs; --"},
        headers=HEADERS,
    )
    # Should either succeed (stored safely) or be rejected — never 500
    assert r.status_code in (201, 400, 422)


@pytest.mark.asyncio
async def test_sql_injection_in_criteria_title(client):
    """SQL injection in criteria titles should be stored safely, not executed."""
    payload = {
        "titles": ["' OR '1'='1"],
        "keywords": [],
        "locations": [],
        "min_salary": None,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": False,
    }
    r = await client.put("/api/settings/criteria", json=payload, headers=HEADERS)
    assert r.status_code == 200
    # Verify it round-trips as a plain string, not executed
    r = await client.get("/api/settings/criteria", headers=HEADERS)
    assert r.json()["titles"] == ["' OR '1'='1"]


# ── Oversized inputs ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_oversized_slug_rejected_or_stored_safely(client):
    """A 1000-character slug should not cause a 500."""
    big_slug = "a" * 1000
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": big_slug},
        headers=HEADERS,
    )
    assert r.status_code != 500


@pytest.mark.asyncio
async def test_oversized_criteria_list(client):
    """Criteria with 200 titles should not crash the server."""
    payload = {
        "titles": [f"Title {i}" for i in range(200)],
        "keywords": [],
        "locations": [],
        "min_salary": None,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": False,
    }
    r = await client.put("/api/settings/criteria", json=payload, headers=HEADERS)
    assert r.status_code != 500


# ── Invalid field types ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_source_type(client):
    """An unsupported job board source should be rejected with 422."""
    r = await client.post(
        "/api/settings/companies",
        json={"source": "linkedin", "slug": "stripe"},
        headers=HEADERS,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_negative_min_salary_rejected(client):
    """Negative salary should be rejected."""
    payload = {
        "titles": [],
        "keywords": [],
        "locations": [],
        "min_salary": -9999,
        "excluded_companies": [],
        "exclude_onsite_outside_major_cities": False,
    }
    r = await client.put("/api/settings/criteria", json=payload, headers=HEADERS)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_string_min_salary_rejected(client):
    """Non-numeric salary should be rejected."""
    r = await client.put(
        "/api/settings/criteria",
        json={
            "titles": [],
            "keywords": [],
            "locations": [],
            "min_salary": "lots",
            "excluded_companies": [],
            "exclude_onsite_outside_major_cities": False,
        },
        headers=HEADERS,
    )
    assert r.status_code == 422


# ── Cross-session data access ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cannot_read_other_sessions_criteria(client):
    """Session A's criteria must not be visible to session B."""
    await client.put(
        "/api/settings/criteria",
        json={
            "titles": ["Secret Title"],
            "keywords": [],
            "locations": [],
            "min_salary": None,
            "excluded_companies": [],
            "exclude_onsite_outside_major_cities": False,
        },
        headers=HEADERS,
    )
    r = await client.get(
        "/api/settings/criteria", headers={"X-Session-ID": "attacker-session"}
    )
    assert "Secret Title" not in r.json().get("titles", [])


@pytest.mark.asyncio
async def test_cannot_delete_other_sessions_company(client):
    """Attempting to delete another session's company must return 404."""
    r = await client.post(
        "/api/settings/companies",
        json={"source": "greenhouse", "slug": "stripe"},
        headers=HEADERS,
    )
    company_id = r.json()["id"]

    r = await client.delete(
        f"/api/settings/companies/{company_id}",
        headers={"X-Session-ID": "attacker-9999"},
    )
    assert r.status_code == 404


# ── Invalid tab / query params ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_jobs_tab(client):
    """An unknown tab value should not crash — return 422 or empty list."""
    r = await client.get("/api/jobs?tab=hacked", headers=HEADERS)
    assert r.status_code in (200, 422)


@pytest.mark.asyncio
async def test_invalid_sector_name(client):
    """An unknown sector name should return 404, not 500."""
    r = await client.post(
        "/api/sectors/add",
        params={"sector_name": "<script>alert(1)</script>"},
        headers=HEADERS,
    )
    assert r.status_code == 404
