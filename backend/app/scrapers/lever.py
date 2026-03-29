from datetime import datetime, timezone
from typing import Any

import httpx

from app.scrapers.base import BaseScraper

_BASE = "https://api.lever.co/v0/postings/{company}?mode=json"


class LeverScraper(BaseScraper):
    async def fetch_jobs(self, slugs: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for slug in slugs:
                try:
                    resp = await client.get(_BASE.format(company=slug))
                    resp.raise_for_status()
                    for job in resp.json():
                        results.append(self.normalize(job, slug))
                except Exception as exc:
                    print(f"[Lever] {slug}: {exc}")
        return results

    def normalize(self, raw: dict[str, Any], slug: str) -> dict[str, Any]:
        # createdAt is Unix ms
        try:
            posted_at = datetime.fromtimestamp(raw.get("createdAt", 0) / 1000, tz=timezone.utc)
        except Exception:
            posted_at = datetime.now(timezone.utc)

        categories = raw.get("categories", {})
        # Lever v0 uses either categories.location (str) or categories.allLocations (list)
        location = categories.get("location", "")
        if not location:
            all_locs = categories.get("allLocations", [])
            location = all_locs[0] if all_locs else ""

        return {
            "external_id": f"lever:{slug}:{raw.get('id', '')}",
            "source": "lever",
            "company_slug": slug,
            "title": raw.get("text", ""),
            "location": location,
            "salary": None,  # Lever postings API doesn't expose salary
            "apply_url": raw.get("hostedUrl", ""),
            "description": raw.get("descriptionPlain", ""),
            "posted_at": posted_at,
        }
