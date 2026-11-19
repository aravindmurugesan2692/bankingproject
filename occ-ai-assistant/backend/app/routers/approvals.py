"""OCC human approval workflow + ServiceNow create-on-approve."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import (
    PRIORITY_FROM_P_CODE,
    ApprovalAction,
    ApprovalAuditEvent,
    Incident,
    IncidentAnalysis,
    IncidentStatus,
    SupportTeam,
    utc_now,
)
from app.routers.analysis import serialize_analysis
from app.schemas import (
    ApprovalAuditRead,
    ApprovalDecide,
    ApprovalDecisionResponse,
    ApprovalDraftUpdate,
    ApprovalPacket,
    IncidentRead,
    PagerDutyPlaceholder,
    SupportTeamRead,
)
from app.schemas import PagerDutyNotificationRead
from app.services import pagerduty as pd
from app.services import servicenow as sn

router = APIRouter(prefix="/approvals", tags=["approvals"])

QUEUE_STATUSES = {
    IncidentStatus.ANALYZED.value,
    IncidentStatus.PENDING_APPROVAL.value,
}


def _slug_list(incident: Incident) -> list[str]:
    raw = incident.selected_team_slugs
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _latest_analysis(db: Session, incident_id: int) -> IncidentAnalysis | None:
    return (
        db.query(IncidentAnalysis)
        .filter(IncidentAnalysis.incident_id == incident_id)
        .order_by(IncidentAnalysis.created_at.desc())
        .first()
    )


def _serialize_audit(event: ApprovalAuditEvent) -> ApprovalAuditRead:
    teams: list[str] = []
    if event.approved_teams:
        try:
            parsed = json.loads(event.approved_teams)
            teams = [str(x) for x in parsed] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            teams = []
    return ApprovalAuditRead(
        id=event.id,
        incident_id=event.incident_id,
        action=event.action,
        actor=event.actor,
        detail=event.detail,
        approved_teams=teams,
        severity=event.severity,
        created_at=event.created_at,
    )


def _add_audit(
    db: Session,
    incident: Incident,
    *,
    action: str,
    actor: str,
    detail: str = "",
    teams: list[str] | None = None,
    severity: str | None = None,
) -> ApprovalAuditEvent:
    event = ApprovalAuditEvent(
        incident_id=incident.id,
        action=action,
        actor=actor,
        detail=detail,
        approved_teams=json.dumps(teams or []),
        severity=severity,
    )
    db.add(event)
    return event


def _teams_for_slugs(db: Session, slugs: list[str]) -> list[SupportTeam]:
    if not slugs:
        return []
    rows = db.query(SupportTeam).filter(SupportTeam.slug.in_(slugs)).all()
    by_slug = {t.slug: t for t in rows}
    return [by_slug[s] for s in slugs if s in by_slug]


def build_packet(db: Session, incident: Incident) -> ApprovalPacket:
    analysis = _latest_analysis(db, incident.id)
    slugs = _slug_list(incident)
    if not slugs and analysis:
        try:
            recommended = json.loads(analysis.recommended_teams)
            slugs = [t["slug"] for t in recommended if "slug" in t]
        except (json.JSONDecodeError, TypeError, KeyError):
            slugs = []
    teams = _teams_for_slugs(db, slugs)
    severity = incident.working_severity or (
        analysis.suggested_priority if analysis else "P3"
    )
    description = incident.working_description or incident.description
    team_names = [t.name for t in teams]
    preview = sn.build_preview(
        incident,
        severity=severity,
        description=description,
        team_names=team_names,
        analysis_summary=analysis.summary if analysis else None,
    )
    pd = [
        PagerDutyPlaceholder(
            team=t.name,
            slug=t.slug,
            service_id=t.pagerduty_service_id,
            escalation_policy_id=t.pagerduty_escalation_policy_id,
        )
        for t in teams
    ]
    audit = (
        db.query(ApprovalAuditEvent)
        .filter(ApprovalAuditEvent.incident_id == incident.id)
        .order_by(ApprovalAuditEvent.created_at.desc())
        .all()
    )
    return ApprovalPacket(
        incident=IncidentRead.model_validate(incident),
        analysis=serialize_analysis(analysis, incident) if analysis else None,
        selected_teams=[SupportTeamRead.model_validate(t) for t in teams],
        pagerduty_placeholders=pd,
        servicenow_preview=preview,
        audit_trail=[_serialize_audit(e) for e in audit],
    )


@router.get("", response_model=list[ApprovalPacket])
def list_approval_queue(db: Session = Depends(get_db)) -> list[ApprovalPacket]:
    rows = (
        db.query(Incident)
        .filter(Incident.status.in_(list(QUEUE_STATUSES)))
        .order_by(Incident.created_at.desc())
        .all()
    )
    return [build_packet(db, row) for row in rows]


@router.get("/{incident_id}", response_model=ApprovalPacket)
def get_approval_packet(incident_id: int, db: Session = Depends(get_db)) -> ApprovalPacket:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return build_packet(db, incident)


@router.patch("/{incident_id}", response_model=ApprovalPacket)
def update_approval_draft(
    incident_id: int, payload: ApprovalDraftUpdate, db: Session = Depends(get_db)
) -> ApprovalPacket:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status not in QUEUE_STATUSES:
        raise HTTPException(status_code=400, detail="Incident is not awaiting approval")

    changes: list[str] = []
    if payload.working_severity is not None:
        incident.working_severity = payload.working_severity
        changes.append(f"severity→{payload.working_severity}")
    if payload.working_description is not None:
        incident.working_description = payload.working_description.strip()
        changes.append("description updated")
    if payload.selected_team_slugs is not None:
        # Validate slugs exist
        known = {
            t.slug
            for t in db.query(SupportTeam)
            .filter(SupportTeam.slug.in_(payload.selected_team_slugs))
            .all()
        }
        cleaned = [s for s in payload.selected_team_slugs if s in known]
        incident.selected_team_slugs = json.dumps(cleaned)
        changes.append(f"teams→{cleaned}")

    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    _add_audit(
        db,
        incident,
        action=ApprovalAction.DRAFT_UPDATE.value,
        actor=payload.actor,
        detail="; ".join(changes),
        teams=_slug_list(incident),
        severity=incident.working_severity,
    )
    db.commit()
    db.refresh(incident)
    return build_packet(db, incident)


@router.post("/{incident_id}/approve", response_model=ApprovalDecisionResponse)
async def approve_incident(
    incident_id: int, payload: ApprovalDecide, db: Session = Depends(get_db)
) -> ApprovalDecisionResponse:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status not in QUEUE_STATUSES and not incident.servicenow_sys_id:
        raise HTTPException(status_code=400, detail="Incident is not awaiting approval")

    # Apply optional last-second edits
    if payload.working_severity is not None:
        incident.working_severity = payload.working_severity
    if payload.working_description is not None:
        incident.working_description = payload.working_description.strip()
    if payload.selected_team_slugs is not None:
        known = {
            t.slug
            for t in db.query(SupportTeam)
            .filter(SupportTeam.slug.in_(payload.selected_team_slugs))
            .all()
        }
        incident.selected_team_slugs = json.dumps(
            [s for s in payload.selected_team_slugs if s in known]
        )

    severity = incident.working_severity or "P3"
    description = incident.working_description or incident.description
    slugs = _slug_list(incident)
    teams = _teams_for_slugs(db, slugs)
    team_names = [t.name for t in teams]
    analysis = _latest_analysis(db, incident.id)

    try:
        sn_result = await sn.create_incident(
            incident,
            severity=severity,
            description=description,
            team_names=team_names,
            analysis_summary=analysis.summary if analysis else None,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"ServiceNow create failed: {exc}") from exc

    incident.servicenow_number = sn_result.number
    incident.servicenow_sys_id = sn_result.sys_id
    incident.servicenow_is_mock = sn_result.is_mock
    incident.approved_by = payload.actor
    incident.approved_at = utc_now()
    incident.status = IncidentStatus.APPROVED.value
    incident.priority = PRIORITY_FROM_P_CODE.get(severity, incident.priority)
    if incident.working_description:
        incident.description = incident.working_description

    _add_audit(
        db,
        incident,
        action=ApprovalAction.APPROVE.value,
        actor=payload.actor,
        detail=f"Approved severity {severity}; teams={team_names}",
        teams=team_names,
        severity=severity,
    )
    _add_audit(
        db,
        incident,
        action=(
            ApprovalAction.SERVICENOW_SKIP_DUPLICATE.value
            if sn_result.duplicate
            else ApprovalAction.SERVICENOW_CREATE.value
        ),
        actor=payload.actor,
        detail=(
            f"{'MOCK ' if sn_result.is_mock else ''}ServiceNow "
            f"{sn_result.number} / {sn_result.sys_id}"
            f"{' (duplicate prevented)' if sn_result.duplicate else ''}"
        ),
        teams=team_names,
        severity=severity,
    )
    db.commit()
    db.refresh(incident)

    # Phase 4 — page approved teams only after explicit OCC approval + SN create
    pd_rows = await pd.notify_approved_teams(
        db, incident, teams, severity=severity
    )
    for row in pd_rows:
        _add_audit(
            db,
            incident,
            action=ApprovalAction.PAGERDUTY_NOTIFY.value,
            actor=payload.actor,
            detail=(
                f"{'MOCK ' if row.is_mock else ''}PagerDuty {row.pd_incident_id} "
                f"→ {row.team_name} ({row.escalation_status})"
            ),
            teams=[row.team_name],
            severity=severity,
        )
    incident.status = IncidentStatus.ACTIVE.value
    db.commit()
    db.refresh(incident)

    audit = (
        db.query(ApprovalAuditEvent)
        .filter(ApprovalAuditEvent.incident_id == incident.id)
        .order_by(ApprovalAuditEvent.created_at.desc())
        .all()
    )
    return ApprovalDecisionResponse(
        incident=IncidentRead.model_validate(incident),
        servicenow_number=sn_result.number,
        servicenow_sys_id=sn_result.sys_id,
        servicenow_is_mock=sn_result.is_mock,
        servicenow_duplicate=sn_result.duplicate,
        pagerduty_notifications=[
            PagerDutyNotificationRead.model_validate(r) for r in pd_rows
        ],
        audit_trail=[_serialize_audit(e) for e in audit],
    )


@router.post("/{incident_id}/reject", response_model=ApprovalDecisionResponse)
def reject_incident(
    incident_id: int, payload: ApprovalDecide, db: Session = Depends(get_db)
) -> ApprovalDecisionResponse:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status not in QUEUE_STATUSES:
        raise HTTPException(status_code=400, detail="Incident is not awaiting approval")
    if not payload.rejection_reason or not payload.rejection_reason.strip():
        raise HTTPException(status_code=422, detail="rejection_reason is required")

    incident.status = IncidentStatus.REJECTED.value
    incident.rejection_reason = payload.rejection_reason.strip()
    incident.approved_by = payload.actor
    incident.approved_at = utc_now()

    _add_audit(
        db,
        incident,
        action=ApprovalAction.REJECT.value,
        actor=payload.actor,
        detail=incident.rejection_reason,
        teams=_slug_list(incident),
        severity=incident.working_severity,
    )
    db.commit()
    db.refresh(incident)

    audit = (
        db.query(ApprovalAuditEvent)
        .filter(ApprovalAuditEvent.incident_id == incident.id)
        .order_by(ApprovalAuditEvent.created_at.desc())
        .all()
    )
    return ApprovalDecisionResponse(
        incident=IncidentRead.model_validate(incident),
        audit_trail=[_serialize_audit(e) for e in audit],
    )
