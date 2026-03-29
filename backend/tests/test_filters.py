"""Tests for US location filtering and pre-scoring logic."""
import pytest
from app.services.filters import is_us_location, title_matches, should_score


class TestIsUsLocation:
    # ── Should pass ──────────────────────────────────────────────────────────
    def test_new_york(self):
        assert is_us_location("New York, NY")

    def test_san_francisco(self):
        assert is_us_location("San Francisco, CA")

    def test_state_abbreviation(self):
        assert is_us_location("Austin, TX")

    def test_full_state_name(self):
        assert is_us_location("Seattle, Washington")

    def test_united_states_explicit(self):
        assert is_us_location("United States")

    def test_us_qualified_remote(self):
        assert is_us_location("Remote - US")

    def test_us_remote_variant(self):
        assert is_us_location("US Remote")

    def test_remote_us_parens(self):
        assert is_us_location("Remote (US)")

    def test_remote_united_states(self):
        assert is_us_location("Remote, United States")

    def test_dc(self):
        assert is_us_location("Washington, DC")

    def test_bay_area(self):
        assert is_us_location("Bay Area, CA")

    def test_mixed_case(self):
        assert is_us_location("new york, ny")

    # ── Should fail ──────────────────────────────────────────────────────────
    def test_london(self):
        assert not is_us_location("London, UK")

    def test_toronto(self):
        assert not is_us_location("Toronto, Canada")

    def test_berlin(self):
        assert not is_us_location("Berlin, Germany")

    def test_remote_no_qualifier(self):
        assert not is_us_location("Remote")

    def test_remote_worldwide(self):
        assert not is_us_location("Remote - Worldwide")

    def test_remote_emea(self):
        assert not is_us_location("Remote - EMEA")

    def test_brazil(self):
        assert not is_us_location("São Paulo, Brazil")

    def test_none_location(self):
        assert not is_us_location(None)

    def test_empty_string(self):
        assert not is_us_location("")

    def test_india(self):
        assert not is_us_location("Bangalore, India")

    def test_singapore(self):
        assert not is_us_location("Singapore")


class TestTitleMatches:
    def test_exact_match(self):
        assert title_matches("Software Engineer", ["Software Engineer"])

    def test_partial_match(self):
        assert title_matches("Senior Software Engineer", ["Software Engineer"])

    def test_case_insensitive(self):
        assert title_matches("BACKEND ENGINEER", ["backend engineer"])

    def test_no_match(self):
        assert not title_matches("Product Manager", ["Software Engineer", "Backend Engineer"])

    def test_empty_desired_returns_true(self):
        assert title_matches("Anything", [])

    def test_multiple_desired_one_matches(self):
        assert title_matches("Full Stack Engineer", ["Backend Engineer", "Full Stack"])


class TestShouldScore:
    def test_us_and_title_match(self):
        assert should_score("Software Engineer", "New York, NY", ["Software Engineer"])

    def test_non_us_excluded(self):
        assert not should_score("Software Engineer", "London, UK", ["Software Engineer"])

    def test_bare_remote_excluded(self):
        assert not should_score("Software Engineer", "Remote", ["Software Engineer"])

    def test_us_remote_included(self):
        assert should_score("Software Engineer", "Remote - US", ["Software Engineer"])

    def test_title_mismatch_excluded(self):
        assert not should_score("Product Manager", "New York, NY", ["Software Engineer"])

    def test_no_desired_titles_passes_title_check(self):
        assert should_score("Anything", "San Francisco, CA", [])
