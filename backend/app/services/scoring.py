import asyncio
import json
import re

import anthropic
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Job, JobScore, SessionCompany, SessionCriteria
from app.services.filters import should_score

_MODEL = "claude-haiku-4-5-20251001"
_MAX_DESC_CHARS = 800

# In-memory progress tracking: session_id -> {"scored": int, "total": int, "done": bool}
scoring_progress: dict[str, dict] = {}


def _build_prompt(job: Job, criteria: dict) -> str:
    desc = (job.description or "")[:_MAX_DESC_CHARS].strip()
    return f"""Score this job listing for a candidate. Reply with ONLY valid JSON: {{"score": <integer 1-100>}}

Candidate criteria:
- Desired titles: {", ".join(criteria.get("titles", []) or ["any"])}
- Required skills/keywords: {", ".join(criteria.get("keywords", []) or ["any"])}
- Preferred locations: {", ".join(criteria.get("locations", []) or ["any"])}
- Minimum salary: {criteria.get("min_salary") or "not specified"}
- Excluded companies: {", ".join(criteria.get("excluded_companies", [])) or "none"}
- Exclude on-site outside major cities: {criteria.get("exclude_onsite_outside_major_cities", True)}

Job:
- Title: {job.title}
- Company: {job.company_slug}
- Location: {job.location}
- Salary: {job.salary or "not listed"}
- Description: {desc}

90-100: Excellent — title fits, most keywords present, location matches
70-89: Good — title close, some keywords, location acceptable
50-69: Partial — adjacent title or partial keywords
30-49: Weak — title/location mismatch
1-29: Poor fit or disqualified"""


def _parse_score(raw: str) -> int:
    """Extract integer score from Claude's response, handling markdown fences and prose."""
    # Strip markdown code fences
    cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
    # Find first JSON object
    m = re.search(r"\{[^}]*\}", cleaned)
    if m:
        return int(json.loads(m.group())["score"])
    # Fallback: find bare integer
    m = re.search(r"\b(\d{1,3})\b", cleaned)
    if m:
        return max(1, min(100, int(m.group(1))))
    raise ValueError(f"Could not parse score from: {raw!r}")


async def score_unscored_jobs(db: AsyncSession, session_id: str) -> int:
    if not settings.anthropic_api_key:
        print("[Scoring] ANTHROPIC_API_KEY not set — skipping.")
        return 0

    companies = (
        await db.execute(
            select(SessionCompany).where(SessionCompany.session_id == session_id)
        )
    ).scalars().all()

    if not companies:
        return 0

    criteria_row = (
        await db.execute(
            select(SessionCriteria).where(SessionCriteria.session_id == session_id)
        )
    ).scalar_one_or_none()

    if not criteria_row:
        return 0

    criteria = {
        "titles": json.loads(criteria_row.titles),
        "keywords": json.loads(criteria_row.keywords),
        "locations": json.loads(criteria_row.locations),
        "min_salary": criteria_row.min_salary,
        "excluded_companies": json.loads(criteria_row.excluded_companies),
        "exclude_onsite_outside_major_cities": criteria_row.exclude_onsite_outside_major_cities,
    }

    # Jobs from this session's companies not yet scored for this session
    slug_filters = [
        (Job.source == sc.source) & (Job.company_slug == sc.slug) for sc in companies
    ]
    already_scored = {
        r.job_id
        for r in (
            await db.execute(
                select(JobScore).where(JobScore.session_id == session_id)
            )
        ).scalars().all()
    }

    desired_titles = json.loads(criteria_row.titles)

    jobs = [
        j
        for j in (
            await db.execute(select(Job).where(or_(*slug_filters)))
        ).scalars().all()
        if j.id not in already_scored
        and should_score(j.title, j.location, desired_titles)
    ]
    print(f"[Scoring] {len(jobs)} jobs pass pre-filter (US + title match)")

    if not jobs:
        return 0

    scoring_progress[session_id] = {"scored": 0, "total": len(jobs), "done": False}

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    sem = asyncio.Semaphore(3)
    results: list[tuple[int, int]] = []
    total_tokens = {"in": 0, "out": 0}

    async def _score_one(job: Job) -> None:
        async with sem:
            try:
                msg = await client.messages.create(
                    model=_MODEL,
                    max_tokens=64,
                    messages=[{"role": "user", "content": _build_prompt(job, criteria)}],
                )
                raw = msg.content[0].text.strip()
                score_val = _parse_score(raw)
                results.append((job.id, score_val))
                scoring_progress[session_id]["scored"] += 1
                tok_in = msg.usage.input_tokens
                tok_out = msg.usage.output_tokens
                total_tokens["in"] += tok_in
                total_tokens["out"] += tok_out
                print(f"[Scoring] {job.company_slug} — {job.title[:50]}: {score_val} ({tok_in}in/{tok_out}out)")
            except Exception as exc:
                scoring_progress[session_id]["scored"] += 1
                print(f"[Scoring] job {job.id} failed ({type(exc).__name__}): {exc}")

    await asyncio.gather(*[_score_one(j) for j in jobs])

    for job_id, score_val in results:
        db.add(JobScore(session_id=session_id, job_id=job_id, score=score_val))

    await db.commit()
    scoring_progress[session_id]["done"] = True
    print(f"[Scoring] Done — {len(results)} scored, {total_tokens['in']} input tokens, {total_tokens['out']} output tokens")
    return len(results)
