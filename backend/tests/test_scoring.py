"""Unit tests for _parse_score — the most brittle part of the scoring pipeline."""
import pytest
from app.services.scoring import _parse_score


# ── Clean JSON ─────────────────────────────────────────────────────────────────

def test_clean_json():
    assert _parse_score('{"score": 75}') == 75

def test_clean_json_with_whitespace():
    assert _parse_score('  { "score" : 82 }  ') == 82

def test_score_at_lower_bound():
    assert _parse_score('{"score": 1}') == 1

def test_score_at_upper_bound():
    assert _parse_score('{"score": 100}') == 100


# ── Markdown fences ────────────────────────────────────────────────────────────

def test_markdown_json_fence():
    assert _parse_score('```json\n{"score": 65}\n```') == 65

def test_plain_code_fence():
    assert _parse_score('```\n{"score": 50}\n```') == 50

def test_fence_with_trailing_newline():
    assert _parse_score('```json\n{"score": 90}\n```\n') == 90


# ── JSON embedded in prose ─────────────────────────────────────────────────────

def test_json_after_prose():
    assert _parse_score('Here is the score: {"score": 78}') == 78

def test_json_before_prose():
    assert _parse_score('{"score": 55} — this job is a partial match.') == 55

def test_json_surrounded_by_prose():
    raw = 'Based on the criteria I would say {"score": 42} for this role.'
    assert _parse_score(raw) == 42


# ── Bare integer fallback ──────────────────────────────────────────────────────

def test_bare_integer():
    assert _parse_score("85") == 85

def test_bare_integer_in_prose():
    assert _parse_score("I would score this job a 72 out of 100.") == 72

def test_bare_integer_clamped_above_100():
    # Should clamp to 100
    assert _parse_score("150") == 100

def test_bare_integer_clamped_below_1():
    # Should clamp to 1
    assert _parse_score("0") == 1

def test_two_digit_score():
    assert _parse_score("42") == 42


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_score_with_extra_json_fields():
    """Claude occasionally adds extra fields — only score should matter."""
    assert _parse_score('{"score": 68, "reason": "good title match"}') == 68

def test_empty_string_raises():
    with pytest.raises((ValueError, KeyError, Exception)):
        _parse_score("")

def test_unparseable_string_raises():
    with pytest.raises((ValueError, KeyError, Exception)):
        _parse_score("no numbers here at all!")

def test_score_99():
    assert _parse_score('{"score": 99}') == 99

def test_score_with_newlines_in_json():
    assert _parse_score('{\n  "score": 77\n}') == 77
