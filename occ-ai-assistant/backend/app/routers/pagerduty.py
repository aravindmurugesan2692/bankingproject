"""PagerDuty notification status APIs (pages only after OCC approval)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    Incident,
    IncidentStatus,
    PagerDutyNotification,
)
from app.schemas import PagerDutyNotificationRead
from app.services.pagerduty import acknowledge_notification

router = APIRouter(prefix="/pagerduty", tags=["pagerduty"])


@router.get("/notifications", response_model=list[PagerDutyNotificationRead])
def list_notifications(db: Session = Depends(get_db)) -> list[PagerDutyNotification]:
    return (
        db.query(PagerDutyNotification)
        .order_by(PagerDutyNotification.notified_at.desc())
        .limit(100)
        .all()
    )


@router.get(
    "/incidents/{incident_id}/notifications",
    response_model=list[PagerDutyNotificationRead],
)
def list_for_incident(
    incident_id: int, db: Session = Depends(get_db)
) -> list[PagerDutyNotification]:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.incident_id == incident_id)
        .order_by(PagerDutyNotification.notified_at.desc())
        .all()
    )


@router.post(
    "/notifications/{notification_id}/acknowledge",
    response_model=PagerDutyNotificationRead,
)
def ack_notification(
    notification_id: int, db: Session = Depends(get_db)
) -> PagerDutyNotification:
    """Record acknowledgement (mock-friendly; live PD sync is best-effort)."""
    row = (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.id == notification_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    updated = acknowledge_notification(db, row)
    incident = db.query(Incident).filter(Incident.id == row.incident_id).first()
    if incident:
        db.add(
            ApprovalAuditEvent(
                incident_id=incident.id,
                action=ApprovalAction.PAGERDUTY_ACK.value,
                actor="System / Responder",
                detail=f"Acknowledged PD {row.pd_incident_id} for {row.team_name}",
                approved_teams=f'["{row.team_name}"]',
            )
        )
        # Rough avg ack helper for dashboard card
        if row.notified_at and updated.acknowledged_at:
            delta = int((updated.acknowledged_at - row.notified_at).total_seconds() / 60)
            incident.ack_minutes = delta
        db.commit()
    return updated


@router.post(
    "/incidents/{incident_id}/notify",
    response_model=list[PagerDutyNotificationRead],
)
async def notify_if_approved(
    incident_id: int, db: Session = Depends(get_db)
) -> list[PagerDutyNotification]:
    """Re-run paging only for already-approved incidents (idempotent)."""
    from app.models import SupportTeam
    from app.services import pagerduty as pd
    import json

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status not in {
        IncidentStatus.APPROVED.value,
        IncidentStatus.ACTIVE.value,
    }:
        raise HTTPException(
            status_code=400,
            detail="PagerDuty notify requires explicit OCC approval first",
        )
    if not incident.approved_at:
        raise HTTPException(status_code=400, detail="Incident was not OCC-approved")

    slugs: list[str] = []
    if incident.selected_team_slugs:
        try:
            slugs = json.loads(incident.selected_team_slugs)
        except json.JSONDecodeError:
            slugs = []
    teams = (
        db.query(SupportTeam).filter(SupportTeam.slug.in_(slugs)).all() if slugs else []
    )
    by_slug = {t.slug: t for t in teams}
    ordered = [by_slug[s] for s in slugs if s in by_slug]
    severity = incident.working_severity or "P3"
    rows = await pd.notify_approved_teams(
        db, incident, ordered, severity=severity
    )
    if incident.status == IncidentStatus.APPROVED.value:
        incident.status = IncidentStatus.ACTIVE.value
        db.commit()
    return rows
