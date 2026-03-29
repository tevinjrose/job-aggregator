from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CompanySource(Base):
    """Global registry of every slug ever added — tracks scrape cache."""
    __tablename__ = "company_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))   # "greenhouse" | "lever"
    slug: Mapped[str] = mapped_column(String(100))
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("source", "slug", name="uq_source_slug"),)


class Job(Base):
    """Global shared job pool — no per-user state here."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True)
    source: Mapped[str] = mapped_column(String(50))
    company_slug: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    salary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    apply_url: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SessionCompany(Base):
    """Which companies each session is tracking."""
    __tablename__ = "session_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    source: Mapped[str] = mapped_column(String(50))
    slug: Mapped[str] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint("session_id", "source", "slug", name="uq_session_source_slug"),
    )


class SessionCriteria(Base):
    """Per-session match criteria."""
    __tablename__ = "session_criteria"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    titles: Mapped[str] = mapped_column(Text, default="[]")
    keywords: Mapped[str] = mapped_column(Text, default="[]")
    locations: Mapped[str] = mapped_column(Text, default="[]")
    min_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excluded_companies: Mapped[str] = mapped_column(Text, default="[]")
    exclude_onsite_outside_major_cities: Mapped[bool] = mapped_column(Boolean, default=True)


class JobScore(Base):
    """Per-session Claude scores — same job can have different scores per user."""
    __tablename__ = "job_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    job_id: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("session_id", "job_id", name="uq_score_session_job"),)


class JobStatus(Base):
    """Per-session job actions: saved / applied / dismissed."""
    __tablename__ = "job_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36))
    job_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("session_id", "job_id", name="uq_status_session_job"),)
