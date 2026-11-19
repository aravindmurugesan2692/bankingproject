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


class DashboardBundle(BaseModel):
    summary: DashboardSummary
    active_incidents: list[IncidentRead]
    recent_incidents: list[IncidentRead]
    priority_distribution: dict[str, int]
    recent_activities: list[dict]
    active_bridges: list[dict]
    pending_acknowledgements: list[dict]
    mock_mode: bool
    data_label: str


class HealthResponse(BaseModel):
    status: str
    app: str
    mock_mode: bool
    llm_configured: bool = False
    servicenow_configured: bool = False


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
    audit_trail: list[ApprovalAuditRead]
