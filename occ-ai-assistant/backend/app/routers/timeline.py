"""Incident timeline APIs — Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, TimelineEvent, TimelineEventAudit
from app.schemas import (
    TimelineCreateRequest,
    TimelineEditRequest,
    TimelineEventAuditRead,
    TimelineEventRead,
)
from app.services import timeline as timeline_svc

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/incidents/{incident_id}", response_model=list[TimelineEventRead])
def list_timeline(
    incident_id: int, db: Session = Depends(get_db)
) -> list[TimelineEvent]:
    if not db.query(Incident).filter(Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")
    return timeline_svc.rebuild_incident_timeline(db, incident_id)


@router.post("/incidents/{incident_id}/rebuild", response_model=list[TimelineEventRead])
def rebuild_timeline(
    incident_id: int, db: Session = Depends(get_db)
) -> list[TimelineEvent]:
    return timeline_svc.rebuild_incident_timeline(db, incident_id)


@router.post("/incidents/{incident_id}", response_model=TimelineEventRead)
def create_timeline_event(
    incident_id: int,
    payload: TimelineCreateRequest,
    db: Session = Depends(get_db),
) -> TimelineEvent:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    occurred = (
        payload.occurred_at.replace(tzinfo=None)
        if payload.occurred_at.tzinfo
        else payload.occurred_at
    )
    return timeline_svc.create_manual_event(
        db,
        incident,
        occurred_at=occurred,
        detail=payload.detail,
        actor=payload.actor,
        team_slug=payload.team_slug,
        team_name=payload.team_name,
        verification_status=payload.verification_status,
        is_mock=payload.is_mock,
    )


@router.patch("/events/{event_id}", response_model=TimelineEventRead)
def edit_timeline_event(
    event_id: int,
    payload: TimelineEditRequest,
    db: Session = Depends(get_db),
) -> TimelineEvent:
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    occurred = None
    if payload.occurred_at is not None:
        occurred = (
            payload.occurred_at.replace(tzinfo=None)
            if payload.occurred_at.tzinfo
            else payload.occurred_at
        )
    return timeline_svc.edit_event(
        db,
        event,
        actor=payload.actor,
        detail=payload.detail,
        occurred_at=occurred,
        verification_status=payload.verification_status,
        team_slug=payload.team_slug,
        team_name=payload.team_name,
    )


@router.get(
    "/events/{event_id}/audits",
    response_model=list[TimelineEventAuditRead],
)
def list_event_audits(
    event_id: int, db: Session = Depends(get_db)
) -> list[TimelineEventAudit]:
    if not db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first():
        raise HTTPException(status_code=404, detail="Timeline event not found")
    return (
        db.query(TimelineEventAudit)
        .filter(TimelineEventAudit.event_id == event_id)
        .order_by(TimelineEventAudit.created_at.desc())
        .all()
    )
