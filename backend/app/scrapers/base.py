from abc import ABC, abstractmethod
from typing import Any


class BaseScraper(ABC):
    @abstractmethod
    async def fetch_jobs(self, slugs: list[str]) -> list[dict[str, Any]]:
        """Fetch and return normalized job dicts for the given company slugs."""
        ...

    @abstractmethod
    def normalize(self, raw: dict[str, Any], slug: str) -> dict[str, Any]:
        """Map a raw API response dict into the shared job schema."""
        ...
