"""Pydantic request/response schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EnvironmentLiteral = Literal["Production", "QA", "Development"]
SeverityLiteral = Literal["P1", "P2", "P3", "P4"]


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=10000)
    application_service: str = Field(..., min_length=1, max_length=255)
    environment: EnvironmentLiteral
    business_impact: str = Field(..., min_length=3, max_length=5000)
    users_affected: int = Field(..., ge=0)
    issue_start_time: datetime
    error_messages: str | None = Field(default=None, max_length=10000)
    affected_infrastructure: str | None = Field(default=None, max_length=5000)
    additional_observations: str | None = Field(default=None, max_length=5000)
    created_by: str | None = Field(default="OCC Engineer", max_length=128)

    @field_validator("title", "description", "application_service", "business_impact")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occ_incident_id: str
    title: str
    description: str
    application_service: str
    environment: str
    business_impact: str
    users_affected: int
    issue_start_time: datetime
    error_messages: str | None
    affected_infrastructure: str | None
    additional_observations: str | None
    status: str
    priority: str
    is_mock: bool
    working_severity: str | None = None
    working_description: str | None = None
    selected_team_slugs: list[str] = []
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    servicenow_number: str | None = None
    servicenow_sys_id: str | None = None
    servicenow_is_mock: bool = True
    ack_minutes: int | None
    resolution_minutes: int | None
    bridge_active: bool
    restored_at: datetime | None = None
    closed_at: datetime | None = None
    rca_status: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str

    @model_validator(mode="before")
    @classmethod
    def coerce_team_slugs(cls, data: Any) -> Any:
        if hasattr(data, "selected_team_slugs"):
            raw = getattr(data, "selected_team_slugs")
            slugs = _parse_slug_list(raw)
            # Build dict from ORM object
            return {
                "id": data.id,
                "occ_incident_id": data.occ_incident_id,
                "title": data.title,
                "description": data.description,
                "application_service": data.application_service,
                "environment": data.environment,
                "business_impact": data.business_impact,
                "users_affected": data.users_affected,
                "issue_start_time": data.issue_start_time,
                "error_messages": data.error_messages,
                "affected_infrastructure": data.affected_infrastructure,
                "additional_observations": data.additional_observations,
                "status": data.status,
                "priority": data.priority,
                "is_mock": data.is_mock,
                "working_severity": getattr(data, "working_severity", None),
                "working_description": getattr(data, "working_description", None),
                "selected_team_slugs": slugs,
                "approved_by": getattr(data, "approved_by", None),
                "approved_at": getattr(data, "approved_at", None),
                "rejection_reason": getattr(data, "rejection_reason", None),
                "servicenow_number": getattr(data, "servicenow_number", None),
                "servicenow_sys_id": getattr(data, "servicenow_sys_id", None),
                "servicenow_is_mock": getattr(data, "servicenow_is_mock", True),
                "ack_minutes": data.ack_minutes,
                "resolution_minutes": data.resolution_minutes,
                "bridge_active": data.bridge_active,
                "restored_at": getattr(data, "restored_at", None),
                "closed_at": getattr(data, "closed_at", None),
                "rca_status": getattr(data, "rca_status", None),
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "created_by": data.created_by,
            }
        if isinstance(data, dict) and "selected_team_slugs" in data:
            data = {**data, "selected_team_slugs": _parse_slug_list(data.get("selected_team_slugs"))}
        return data


def _parse_slug_list(raw: Any) -> list[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (TypeError, json.JSONDecodeError):
        pass
    return []


class DashboardSummary(BaseModel):
    total_incidents: int
    active_incidents: int
    critical_incidents: int
    pending_approvals: int
    active_bridges: int
    resolved_incidents: int
    avg_ack_minutes: float | None
    avg_resolution_minutes: float | None
    mock_mode: bool
    data_label: str


class PagerDutyNotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    servicenow_number: str | None
    team_slug: str
    team_name: str
    pagerduty_service_id: str
    pagerduty_escalation_policy_id: str
    pd_incident_id: str
    pd_incident_url: str
    escalation_status: str
    notified_at: datetime
    acknowledged_at: datetime | None
    is_mock: bool
    created_at: datetime


class TeamsBridgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    servicenow_number: str | None
    bridge_code: str
    title: str
    provider: str
    meeting_id: str
    meeting_url: str
    status: str
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    invited_responders: list[dict] = []
    invited_count: int = 0
    invited_at: datetime | None
    is_mock: bool
    created_by: str


class BridgeCreateRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    bridge_code: str | None = Field(default=None, max_length=32)
    invite: bool = True
    incident_id: int | None = None


class BridgeActorRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class BridgeInviteRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    responders: list[dict] | None = None


class DashboardBundle(BaseModel):
    summary: DashboardSummary
    active_incidents: list[IncidentRead]
    recent_incidents: list[IncidentRead]
    priority_distribution: dict[str, int]
    recent_activities: list[dict]
    active_bridges: list[dict]
    pending_acknowledgements: list[dict]
    pagerduty_notifications: list[PagerDutyNotificationRead] = []
    teams_bridges: list[TeamsBridgeRead] = []
    mock_mode: bool
    data_label: str


class HealthResponse(BaseModel):
    status: str
    app: str
    mock_mode: bool
    llm_configured: bool = False
    servicenow_configured: bool = False
    pagerduty_configured: bool = False
    microsoft_graph_configured: bool = False


class BridgeNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    bridge_id: int | None
    note_type: str
    title: str
    content: str
    occurred_at: datetime | None
    status: str
    approved_by: str | None
    approved_at: datetime | None
    is_mock: bool
    created_by: str
    created_at: datetime


class BridgeNoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=3, max_length=20000)
    title: str = Field(default="", max_length=255)
    note_type: Literal["manual", "transcript_excerpt"] = "manual"
    occurred_at: datetime | None = None
    bridge_id: int | None = None
    approve_now: bool = True
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    is_mock: bool = False


class BridgeNoteActorRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class BridgeAIUpdateRead(BaseModel):
    id: int
    incident_id: int
    occ_incident_id: str
    summary: str
    key_points: list[str]
    open_questions: list[str]
    next_actions: list[str]
    hypotheses: list[str]
    source_note_ids: list[int]
    root_cause_status: str
    disclaimer: str
    provider: str
    model: str
    is_mock: bool
    created_by: str
    created_at: datetime


class BridgeAIGenerateRequest(BaseModel):
    note_ids: list[int] | None = None
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class WorkNoteDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    bridge_update_id: int | None
    content: str
    content_hash: str
    status: str
    servicenow_number: str | None
    servicenow_sys_id: str | None
    is_mock: bool
    approved_by: str | None
    approved_at: datetime | None
    posted_at: datetime | None
    posted_by: str | None
    created_by: str
    created_at: datetime


class WorkNoteActorRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class WorkNotePostResponse(BaseModel):
    draft: WorkNoteDraftRead
    duplicate: bool
    is_mock: bool


class ResponderDirectoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    email: str
    team_slug: str
    team_name: str
    role: str
    active: bool
    is_mock: bool


class BridgeAttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    bridge_id: int
    occ_incident_id: str
    display_name: str
    email: str
    team_slug: str | None
    team_name: str | None
    event_kind: str
    joined_at: datetime
    left_at: datetime | None
    source: str
    verification_status: str
    is_mock: bool
    notes: str | None
    recorded_by: str
    created_at: datetime


class AttendanceCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128)
    joined_at: datetime
    email: str = Field(default="", max_length=255)
    team_slug: str | None = None
    team_name: str | None = None
    left_at: datetime | None = None
    event_kind: Literal["teams_join", "attendance_confirmed"] = "teams_join"
    notes: str | None = Field(default=None, max_length=2000)
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class AttendanceActorRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    event_type: str
    occurred_at: datetime
    actor: str
    team_slug: str | None
    team_name: str | None
    detail: str
    verification_status: str
    source_system: str
    source_ref: str | None
    is_mock: bool
    editable: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


class TimelineEventAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    actor: str
    change_summary: str
    before_json: str | None
    after_json: str | None
    created_at: datetime


class TimelineCreateRequest(BaseModel):
    occurred_at: datetime
    detail: str = Field(..., min_length=3, max_length=5000)
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    team_slug: str | None = None
    team_name: str | None = None
    verification_status: Literal["unverified", "verified"] = "unverified"
    is_mock: bool = False


class TimelineEditRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    detail: str | None = Field(default=None, max_length=5000)
    occurred_at: datetime | None = None
    verification_status: Literal["unverified", "verified", "edited"] | None = None
    team_slug: str | None = None
    team_name: str | None = None


class ParticipationRow(BaseModel):
    display_name: str
    email: str = ""
    team_slug: str | None = None
    team_name: str | None = None
    pd_notified: bool = False
    pd_notified_at: datetime | None = None
    pd_acknowledged: bool = False
    pd_acknowledged_at: datetime | None = None
    teams_joined: bool = False
    teams_joined_at: datetime | None = None
    attendance_confirmed: bool = False
    attendance_confirmed_at: datetime | None = None
    is_mock: bool = False


class RecommendedTeam(BaseModel):
    team: str
    slug: str
    reason: str


class SupportTeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str
    ownership: str
    responsibilities: str
    pagerduty_service_id: str
    pagerduty_escalation_policy_id: str
    active: bool


class IncidentAnalysisRead(BaseModel):
    id: int
    incident_id: int
    occ_incident_id: str | None = None
    incident_title: str | None = None
    summary: str
    category: str
    suggested_priority: str
    business_impact: str
    potential_causes: list[str]
    affected_application: str
    recommended_teams: list[RecommendedTeam]
    troubleshooting_steps: list[str]
    missing_information: list[str]
    next_actions: list[str]
    needs_more_info: bool
    disclaimer: str
    provider: str
    model: str
    is_mock: bool
    created_at: datetime


class IncidentCreateResponse(BaseModel):
    incident: IncidentRead
    analysis: IncidentAnalysisRead | None = None


class ApprovalAuditRead(BaseModel):
    id: int
    incident_id: int
    action: str
    actor: str
    detail: str
    approved_teams: list[str] = []
    severity: str | None = None
    created_at: datetime


class PagerDutyPlaceholder(BaseModel):
    team: str
    slug: str
    service_id: str
    escalation_policy_id: str


class ApprovalPacket(BaseModel):
    incident: IncidentRead
    analysis: IncidentAnalysisRead | None
    selected_teams: list[SupportTeamRead]
    pagerduty_placeholders: list[PagerDutyPlaceholder]
    servicenow_preview: dict
    audit_trail: list[ApprovalAuditRead]


class ApprovalDraftUpdate(BaseModel):
    working_severity: SeverityLiteral | None = None
    working_description: str | None = Field(default=None, min_length=10, max_length=10000)
    selected_team_slugs: list[str] | None = None
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class ApprovalDecide(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    rejection_reason: str | None = Field(default=None, max_length=5000)
    working_severity: SeverityLiteral | None = None
    working_description: str | None = None
    selected_team_slugs: list[str] | None = None


class ApprovalDecisionResponse(BaseModel):
    incident: IncidentRead
    servicenow_number: str | None = None
    servicenow_sys_id: str | None = None
    servicenow_is_mock: bool = True
    servicenow_duplicate: bool = False
    pagerduty_notifications: list[PagerDutyNotificationRead] = []
    audit_trail: list[ApprovalAuditRead]


# --- Phase 8: closure + incident management / reporting ---


class IncidentClosureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    occ_incident_id: str
    status: str
    restored_at: datetime | None
    final_summary: str
    timeline_summary: str
    team_notes: str
    remediation_notes: str
    rca_status: str
    rca_statement: str
    submitted_by: str | None
    submitted_at: datetime | None
    approved_by: str | None
    approved_at: datetime | None
    rejected_by: str | None
    rejected_at: datetime | None
    rejection_reason: str | None
    servicenow_resolved: bool
    servicenow_resolve_mock: bool
    pagerduty_resolved: bool
    pagerduty_resolve_mock: bool
    sync_detail: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ClosureDraftUpdate(BaseModel):
    restored_at: datetime | None = None
    final_summary: str | None = Field(default=None, max_length=20000)
    timeline_summary: str | None = Field(default=None, max_length=50000)
    team_notes: str | None = Field(default=None, max_length=20000)
    remediation_notes: str | None = Field(default=None, max_length=20000)
    rca_status: Literal["unconfirmed", "confirmed"] | None = None
    rca_statement: str | None = Field(default=None, max_length=10000)
    refresh_timeline: bool = False
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)


class ClosureActorRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    close_fully: bool = True


class ClosureRejectRequest(BaseModel):
    actor: str = Field(default="OCC Engineer · Demo User", max_length=128)
    reason: str = Field(..., min_length=3, max_length=5000)


class ManagementHistoryItem(BaseModel):
    id: int
    occ_incident_id: str
    servicenow_number: str | None
    pagerduty_incident_ids: list[str] = []
    title: str
    application_service: str
    environment: str
    priority: str
    working_severity: str | None = None
    status: str
    assigned_teams: list[str] = []
    created_at: datetime
    issue_start_time: datetime
    ack_minutes: int | None
    resolution_minutes: int | None
    bridge_duration_minutes: int | None = None
    restored_at: datetime | None = None
    closed_at: datetime | None = None
    rca_status: str | None = None
    is_mock: bool
    closure_status: str | None = None


class ManagementHistoryResponse(BaseModel):
    total: int
    items: list[ManagementHistoryItem]
    data_label: str
    mock_mode: bool


class ManagementDetail(BaseModel):
    incident: IncidentRead
    pagerduty_incident_ids: list[str] = []
    assigned_teams: list[str] = []
    bridge_duration_minutes: int | None = None
    closure: IncidentClosureRead | None = None
    timeline_event_count: int = 0
    analysis_category: str | None = None
    is_mock: bool
    data_label: str


class ReportingMetrics(BaseModel):
    """Reporting from real app data — seeded rows labeled MOCK via is_mock / data_label."""

    total_incidents: int
    by_category: list[dict[str, Any]]
    by_support_team: list[dict[str, Any]]
    avg_ack_minutes: float | None
    avg_resolution_minutes: float | None
    repeat_incidents: list[dict[str, Any]]
    volume_by_application: list[dict[str, Any]]
    volume_by_severity: list[dict[str, Any]]
    team_participation: list[dict[str, Any]]
    sla_trends: list[dict[str, Any]]
    closed_count: int
    pending_closure_count: int
    mock_incident_count: int
    live_incident_count: int
    data_label: str
    mock_mode: bool
