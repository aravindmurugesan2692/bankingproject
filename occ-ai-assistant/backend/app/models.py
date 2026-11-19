"""SQLAlchemy ORM models."""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Environment(str, PyEnum):
    PRODUCTION = "Production"
    QA = "QA"
    DEVELOPMENT = "Development"


class IncidentStatus(str, PyEnum):
    NEW = "New"
    ANALYZED = "Analyzed"
    ACTIVE = "Active"
    PENDING_APPROVAL = "Pending Approval"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class IncidentPriority(str, PyEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


PRIORITY_FROM_P_CODE = {
    "P1": IncidentPriority.CRITICAL.value,
    "P2": IncidentPriority.HIGH.value,
    "P3": IncidentPriority.MEDIUM.value,
    "P4": IncidentPriority.LOW.value,
}


class SupportTeam(Base):
    __tablename__ = "support_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ownership: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[str] = mapped_column(Text, nullable=False)
    pagerduty_service_id: Mapped[str] = mapped_column(String(128), default="")
    pagerduty_escalation_policy_id: Mapped[str] = mapped_column(String(128), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    keywords: Mapped[str] = mapped_column(Text, default="")  # comma-separated matching hints
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    application_service: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    users_affected: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_messages: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_infrastructure: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_observations: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(64), default=IncidentStatus.NEW.value)
    priority: Mapped[str] = mapped_column(String(32), default=IncidentPriority.MEDIUM.value)
    is_mock: Mapped[bool] = mapped_column(default=False)

    ack_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bridge_active: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")

    analyses: Mapped[list["IncidentAnalysis"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentAnalysis(Base):
    __tablename__ = "incident_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    suggested_priority: Mapped[str] = mapped_column(String(8), nullable=False)  # P1–P4
    business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    potential_causes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    affected_application: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_teams: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of {team,reason,slug}
    troubleshooting_steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    missing_information: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    next_actions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    needs_more_info: Mapped[bool] = mapped_column(Boolean, default=False)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default=(
            "AI recommendations are hypotheses for OCC review — not confirmed root cause."
        ),
    )
    provider: Mapped[str] = mapped_column(String(64), default="heuristic")
    model: Mapped[str] = mapped_column(String(128), default="mock-heuristic-v1")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="analyses")
