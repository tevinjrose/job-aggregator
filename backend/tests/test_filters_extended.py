"""Extended edge-case tests for is_us_location."""
import pytest
from app.services.filters import is_us_location


# ── City-only (no state) ───────────────────────────────────────────────────────

def test_austin_city_only():
    assert is_us_location("Austin") is True

def test_portland_city_only():
    assert is_us_location("Portland") is True

def test_nashville_city_only():
    assert is_us_location("Nashville") is True

def test_seattle_city_only():
    assert is_us_location("Seattle") is True


# ── Ambiguous state names ──────────────────────────────────────────────────────

def test_washington_state():
    assert is_us_location("Washington") is True

def test_washington_dc():
    assert is_us_location("Washington, DC") is True

def test_washington_dc_spelled_out():
    # "washington" matches US_STATES so this correctly returns True
    assert is_us_location("Washington, D.C.") is True

def test_georgia_state():
    # "georgia" matches US_STATES — acceptable false positive for Georgia (country)
    assert is_us_location("Georgia") is True

def test_new_york_city_only():
    assert is_us_location("New York") is True


# ── City, State patterns ───────────────────────────────────────────────────────

def test_austin_tx():
    assert is_us_location("Austin, TX") is True

def test_portland_or():
    assert is_us_location("Portland, OR") is True

def test_new_york_ny():
    assert is_us_location("New York, NY") is True

def test_san_francisco_ca():
    assert is_us_location("San Francisco, CA") is True

def test_city_full_state_name():
    assert is_us_location("Austin, Texas") is True

def test_city_full_state_lowercase():
    assert is_us_location("austin, texas") is True


# ── Hybrid / multi-location strings ───────────────────────────────────────────

def test_hybrid_san_francisco():
    assert is_us_location("Hybrid - San Francisco") is True

def test_hybrid_new_york():
    assert is_us_location("New York / Remote") is True

def test_multiple_us_cities():
    assert is_us_location("New York or San Francisco") is True

def test_onsite_or_remote_us():
    assert is_us_location("On-site or Remote (US)") is True


# ── Non-US that could be confused ─────────────────────────────────────────────

def test_ontario_canada():
    # "Ontario, CA" is a real city in California — should match as US
    assert is_us_location("Ontario, CA") is True

def test_london_uk():
    assert is_us_location("London, UK") is False

def test_paris_france():
    assert is_us_location("Paris, France") is False

def test_toronto_canada():
    assert is_us_location("Toronto, Canada") is False

def test_sydney_australia():
    assert is_us_location("Sydney, Australia") is False

def test_berlin_germany():
    assert is_us_location("Berlin, Germany") is False

def test_apac():
    assert is_us_location("APAC") is False

def test_emea():
    assert is_us_location("EMEA") is False

def test_worldwide():
    assert is_us_location("Worldwide") is False

def test_global():
    assert is_us_location("Global") is False


# ── Fully remote variants ──────────────────────────────────────────────────────

def test_remote_us_slash():
    assert is_us_location("Remote / US") is True

def test_remote_usa_parens():
    assert is_us_location("Remote (USA)") is True

def test_remote_no_country():
    assert is_us_location("Remote") is False

def test_remote_worldwide():
    assert is_us_location("Remote - Worldwide") is False

def test_remote_europe():
    assert is_us_location("Remote - Europe") is False
