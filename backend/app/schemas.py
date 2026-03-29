from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Company sources ────────────────────────────────────────────────────────────

class SessionCompanyOut(BaseModel):
    id: int
    source: str
    slug: str
    last_scraped_at: datetime | None = None

    model_config = {"from_attributes": True}


class SessionCompanyCreate(BaseModel):
    source: Literal["greenhouse", "lever"]
    slug: str


class CompanyDirectoryOut(BaseModel):
    source: Literal["greenhouse", "lever"]
    slug: str
    label: str


# ── User criteria ──────────────────────────────────────────────────────────────

class UserCriteriaIn(BaseModel):
    titles: list[str] = []
    keywords: list[str] = []
    locations: list[str] = []
    min_salary: int | None = Field(default=None, ge=0)
    excluded_companies: list[str] = []
    exclude_onsite_outside_major_cities: bool = True


class UserCriteriaOut(UserCriteriaIn):
    pass


# ── Jobs ───────────────────────────────────────────────────────────────────────

class JobOut(BaseModel):
    id: int
    external_id: str
    source: str
    company_slug: str
    title: str
    location: str
    salary: str | None
    apply_url: str
    posted_at: datetime
    score: int | None
    status: str | None


class JobStatusUpdate(BaseModel):
    status: Literal["applied", "saved", "dismissed"] | None
