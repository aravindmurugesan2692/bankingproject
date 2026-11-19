"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EnvironmentLiteral = Literal["Production", "QA", "Development"]


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
    ack_minutes: int | None
    resolution_minutes: int | None
    bridge_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str


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
