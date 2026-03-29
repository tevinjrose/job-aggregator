from datetime import datetime, timezone
from typing import Any

import httpx

from app.scrapers.base import BaseScraper

# ?content=true fetches the full job description
_BASE = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


class GreenhouseScraper(BaseScraper):
    async def fetch_jobs(self, slugs: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for slug in slugs:
                try:
                    resp = await client.get(_BASE.format(board=slug))
                    resp.raise_for_status()
                    for job in resp.json().get("jobs", []):
                        results.append(self.normalize(job, slug))
                except Exception as exc:
                    print(f"[Greenhouse] {slug}: {exc}")
        return results

    def normalize(self, raw: dict[str, Any], slug: str) -> dict[str, Any]:
        posted_raw = raw.get("updated_at") or raw.get("created_at", "")
        try:
            posted_at = datetime.fromisoformat(posted_raw)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
        except Exception:
            posted_at = datetime.now(timezone.utc)

        location = raw.get("location", {})
        location_name = location.get("name", "") if isinstance(location, dict) else str(location)

        return {
            "external_id": f"greenhouse:{slug}:{raw.get('id', '')}",
            "source": "greenhouse",
            "company_slug": slug,
            "title": raw.get("title", ""),
            "location": location_name,
            "salary": None,  # Greenhouse board API doesn't expose salary
            "apply_url": raw.get("absolute_url", ""),
            "description": raw.get("content", ""),
            "posted_at": posted_at,
        }
