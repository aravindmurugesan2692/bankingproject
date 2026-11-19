"""SQLAlchemy ORM models."""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Environment(str, PyEnum):
    PRODUCTION = "Production"
    QA = "QA"
    DEVELOPMENT = "Development"


class IncidentStatus(str, PyEnum):
    NEW = "New"
    ACTIVE = "Active"
    PENDING_APPROVAL = "Pending Approval"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class IncidentPriority(str, PyEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


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
