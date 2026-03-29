"""
Shared pre-filtering logic used by both the scoring service and the jobs router.
"""

US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming", "washington dc", "district of columbia",
}

US_STATE_ABBREVS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi",
    "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi",
    "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc",
    "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut",
    "vt", "va", "wa", "wv", "wi", "wy", "dc",
}

US_CITY_HINTS = {
    "new york", "san francisco", "los angeles", "chicago", "austin",
    "seattle", "boston", "denver", "atlanta", "miami", "dallas",
    "houston", "phoenix", "portland", "san diego", "philadelphia",
    "minneapolis", "detroit", "nashville", "charlotte", "raleigh",
    "salt lake", "pittsburgh", "baltimore", "las vegas", "san jose",
    "brooklyn", "manhattan", "silicon valley", "bay area",
}

US_REMOTE_HINTS = {"us remote", "remote us", "remote - us", "remote (us",
                   "remote – us", "united states remote", "remote, us",
                   "remote / us", "remote/us"}


def is_us_location(location: str | None) -> bool:
    """Return True if the location is US-based (including US-qualified remote)."""
    if not location:
        return False

    loc = location.lower().strip()

    # Explicit US identifiers
    if any(k in loc for k in ("united states", " usa", "(usa)", ", usa", "u.s.a")):
        return True

    # US-qualified remote — also accept "City / Remote" hybrid patterns
    if "remote" in loc:
        if any(hint in loc for hint in US_REMOTE_HINTS):
            return True
        if any(city in loc for city in US_CITY_HINTS):
            return True
        if any(state in loc for state in US_STATES):
            return True
        return False

    # State name or abbreviation
    if any(state in loc for state in US_STATES):
        return True

    # City hints
    if any(city in loc for city in US_CITY_HINTS):
        return True

    # Comma-separated "City, ST" pattern (e.g. "Austin, TX")
    parts = [p.strip() for p in loc.split(",")]
    if len(parts) >= 2 and parts[-1].strip() in US_STATE_ABBREVS:
        return True

    return False


def title_matches(title: str, desired: list[str]) -> bool:
    """Return True if title contains any of the desired title keywords."""
    if not desired:
        return True
    t = title.lower()
    return any(d.lower() in t for d in desired)


def should_score(title: str, location: str | None, desired_titles: list[str]) -> bool:
    """
    Pre-scoring gate: only score a job if it passes title and US location checks.
    This avoids wasting tokens on irrelevant or non-US listings.
    """
    return is_us_location(location) and title_matches(title, desired_titles)
