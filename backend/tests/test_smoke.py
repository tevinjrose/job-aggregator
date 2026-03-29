"""
Smoke test against the live Railway deployment.
Skipped automatically if JOBRADAR_API_URL is not set.

Run manually:
    JOBRADAR_API_URL=https://job-aggregator-production-0ef1.up.railway.app \
    python3 -m pytest backend/tests/test_smoke.py -v
"""
import os
import pytest
import httpx

LIVE_URL = os.getenv("JOBRADAR_API_URL", "").rstrip("/")

pytestmark = pytest.mark.skipif(
    not LIVE_URL,
    reason="JOBRADAR_API_URL not set — skipping live smoke tests",
)


def test_health_endpoint_returns_ok():
    r = httpx.get(f"{LIVE_URL}/health", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_criteria_endpoint_reachable():
    r = httpx.get(
        f"{LIVE_URL}/api/settings/criteria",
        headers={"X-Session-ID": "smoke-test-session"},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "titles" in data


def test_companies_endpoint_reachable():
    r = httpx.get(
        f"{LIVE_URL}/api/settings/companies",
        headers={"X-Session-ID": "smoke-test-session"},
        timeout=10,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sectors_endpoint_reachable():
    r = httpx.get(
        f"{LIVE_URL}/api/sectors",
        headers={"X-Session-ID": "smoke-test-session"},
        timeout=10,
    )
    assert r.status_code == 200
    assert "Fintech" in r.json()


def test_scraper_status_reachable():
    r = httpx.get(
        f"{LIVE_URL}/api/scraper/status",
        headers={"X-Session-ID": "smoke-test-session"},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("idle", "scoring", "done")
