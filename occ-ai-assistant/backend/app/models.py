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
    PENDING_APPROVAL = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ACTIVE = "Active"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class ApprovalAction(str, PyEnum):
    DRAFT_UPDATE = "draft_update"
    APPROVE = "approve"
    REJECT = "reject"
    SERVICENOW_CREATE = "servicenow_create"
    SERVICENOW_SKIP_DUPLICATE = "servicenow_skip_duplicate"
    PAGERDUTY_NOTIFY = "pagerduty_notify"
    PAGERDUTY_ACK = "pagerduty_ack"
    BRIDGE_CREATE = "bridge_create"
    BRIDGE_OPEN = "bridge_open"
    BRIDGE_END = "bridge_end"
    BRIDGE_INVITE = "bridge_invite"
    ATTENDANCE_RECORD = "attendance_record"
    ATTENDANCE_CONFIRM = "attendance_confirm"
    TIMELINE_CREATE = "timeline_create"
    TIMELINE_EDIT = "timeline_edit"
    BRIDGE_NOTE_ADD = "bridge_note_add"
    BRIDGE_NOTE_APPROVE = "bridge_note_approve"
    BRIDGE_AI_GENERATE = "bridge_ai_generate"
    WORKNOTE_PREVIEW = "worknote_preview"
    WORKNOTE_APPROVE = "worknote_approve"
    WORKNOTE_POST = "worknote_post"
    WORKNOTE_SKIP_DUPLICATE = "worknote_skip_duplicate"


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

    # Phase 3 — OCC approval working copy (editable before approve)
    working_severity: Mapped[str | None] = mapped_column(String(8), nullable=True)  # P1–P4
    working_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_team_slugs: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ServiceNow linkage (set only after explicit approval)
    servicenow_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    servicenow_sys_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    servicenow_is_mock: Mapped[bool] = mapped_column(Boolean, default=True)

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
    approval_events: Mapped[list["ApprovalAuditEvent"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    pagerduty_notifications: Mapped[list["PagerDutyNotification"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    teams_bridges: Mapped[list["TeamsBridge"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    bridge_attendances: Mapped[list["BridgeAttendance"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    bridge_notes: Mapped[list["BridgeNote"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    bridge_ai_updates: Mapped[list["BridgeAIUpdate"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    work_note_drafts: Mapped[list["WorkNoteDraft"]] = relationship(
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


class ApprovalAuditEvent(Base):
    __tablename__ = "approval_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    approved_teams: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    severity: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="approval_events")


class PagerDutyNotification(Base):
    """Per-team PagerDuty page created only after OCC approval."""

    __tablename__ = "pagerduty_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)
    servicenow_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    team_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    team_name: Mapped[str] = mapped_column(String(128), nullable=False)
    pagerduty_service_id: Mapped[str] = mapped_column(String(128), default="")
    pagerduty_escalation_policy_id: Mapped[str] = mapped_column(String(128), default="")

    pd_incident_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pd_incident_url: Mapped[str] = mapped_column(String(512), default="")
    escalation_status: Mapped[str] = mapped_column(
        String(64), default="notified"
    )  # notified | acknowledged | escalated | failed

    notified_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="pagerduty_notifications")


class TeamsBridge(Base):
    """Teams (or mock) conference bridge linked to an OCC incident.

    Timestamps are set only when the corresponding action occurs —
    do not fabricate start/end or invent live attendance (Phase 6).
    """

    __tablename__ = "teams_bridges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)
    servicenow_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    bridge_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="mock")  # mock | microsoft_graph

    meeting_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    meeting_url: Mapped[str] = mapped_column(String(1024), default="")
    status: Mapped[str] = mapped_column(
        String(32), default="created"
    )  # created | open | ended

    # created_at always set; started_at / ended_at only on open / end actions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Invited responders (JSON list of {name, team_slug, email?}) — not live attendance
    invited_responders: Mapped[str | None] = mapped_column(Text, nullable=True)
    invited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")

    incident: Mapped["Incident"] = relationship(back_populates="teams_bridges")
    attendances: Mapped[list["BridgeAttendance"]] = relationship(
        back_populates="bridge", cascade="all, delete-orphan"
    )


class ResponderDirectory(Base):
    """User → support-team mapping for participation attribution."""

    __tablename__ = "responder_directory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    team_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    team_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="responder")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class BridgeAttendance(Base):
    """Who joined a Teams bridge and when.

    Timestamps must come from Graph, explicit OCC entry, or clearly labeled
    MOCK sample offsets from a real bridge.started_at — never invented silently.
    """

    __tablename__ = "bridge_attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    bridge_id: Mapped[int] = mapped_column(ForeignKey("teams_bridges.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)

    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="")
    team_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    team_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Distinct participation kinds (not PD notify/ack)
    event_kind: Mapped[str] = mapped_column(
        String(64), default="teams_join"
    )  # teams_join | attendance_confirmed

    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    source: Mapped[str] = mapped_column(
        String(64), default="mock_sample"
    )  # mock_sample | graph | manual
    verification_status: Mapped[str] = mapped_column(
        String(64), default="unverified"
    )  # unverified | confirmed | disputed

    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="bridge_attendances")
    bridge: Mapped["TeamsBridge"] = relationship(back_populates="attendances")


class TimelineEvent(Base):
    """Unified incident timeline with verification + edit audit."""

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)

    # pd_notify | pd_ack | teams_join | attendance_confirmed | bridge_create |
    # bridge_open | bridge_end | bridge_invite | manual
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    actor: Mapped[str] = mapped_column(String(128), default="")
    team_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    team_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")

    verification_status: Mapped[str] = mapped_column(
        String(64), default="unverified"
    )  # unverified | verified | edited

    source_system: Mapped[str] = mapped_column(
        String(64), default="manual"
    )  # pagerduty | teams | approval | manual | mock_sample
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    editable: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="timeline_events")
    audits: Mapped[list["TimelineEventAudit"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class TimelineEventAudit(Base):
    """Audit trail for timeline edits — never silent rewrites."""

    __tablename__ = "timeline_event_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("timeline_events.id"), index=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    event: Mapped["TimelineEvent"] = relationship(back_populates="audits")


class BridgeNote(Base):
    """OCC-approved bridge transcript excerpt or manual note.

    AI Bridge Assistant may only use notes that are approved.
    Never invent bridge activities — content must be OCC-supplied.
    """

    __tablename__ = "bridge_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)
    bridge_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams_bridges.id"), nullable=True, index=True
    )

    note_type: Mapped[str] = mapped_column(
        String(64), default="manual"
    )  # manual | transcript_excerpt
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # When the note claims the activity occurred — OCC-provided, not invented
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default="draft"
    )  # draft | approved | rejected
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="bridge_notes")


class BridgeAIUpdate(Base):
    """Structured AI bridge update generated only from approved notes."""

    __tablename__ = "bridge_ai_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    open_questions: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    next_actions: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    hypotheses: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    source_note_ids: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of ints

    root_cause_status: Mapped[str] = mapped_column(
        String(64), default="unconfirmed"
    )  # unconfirmed | insufficient_evidence
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)

    provider: Mapped[str] = mapped_column(String(64), default="heuristic")
    model: Mapped[str] = mapped_column(String(128), default="mock-bridge-assistant-v1")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="bridge_ai_updates")
    work_notes: Mapped[list["WorkNoteDraft"]] = relationship(
        back_populates="bridge_update", cascade="all, delete-orphan"
    )


class WorkNoteDraft(Base):
    """ServiceNow work-note preview / post — post only after OCC approve; dedupe."""

    __tablename__ = "work_note_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    occ_incident_id: Mapped[str] = mapped_column(String(32), index=True)
    bridge_update_id: Mapped[int | None] = mapped_column(
        ForeignKey("bridge_ai_updates.id"), nullable=True, index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(32), default="preview"
    )  # preview | approved | posted | skipped_duplicate

    servicenow_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    servicenow_sys_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)

    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    posted_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_by: Mapped[str] = mapped_column(String(128), default="OCC Engineer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="work_note_drafts")
    bridge_update: Mapped["BridgeAIUpdate | None"] = relationship(
        back_populates="work_notes"
    )
