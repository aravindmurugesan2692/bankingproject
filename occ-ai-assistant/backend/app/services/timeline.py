"""Unified incident timeline — sync from PD/bridge/attendance + editable entries."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    BridgeAttendance,
    Incident,
    PagerDutyNotification,
    TeamsBridge,
    TimelineEvent,
    TimelineEventAudit,
    utc_now,
)

EVENT_TYPES = {
    "pd_notify",
    "pd_ack",
    "teams_join",
    "attendance_confirmed",
    "bridge_create",
    "bridge_open",
    "bridge_end",
    "bridge_invite",
    "manual",
}


def _snapshot(event: TimelineEvent) -> dict[str, Any]:
    return {
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "actor": event.actor,
        "team_slug": event.team_slug,
        "team_name": event.team_name,
        "detail": event.detail,
        "verification_status": event.verification_status,
    }


def _find_by_source(
    db: Session, incident_id: int, source_system: str, source_ref: str
) -> TimelineEvent | None:
    return (
        db.query(TimelineEvent)
        .filter(
            TimelineEvent.incident_id == incident_id,
            TimelineEvent.source_system == source_system,
            TimelineEvent.source_ref == source_ref,
        )
        .first()
    )


def ensure_event(
    db: Session,
    incident: Incident,
    *,
    event_type: str,
    occurred_at: datetime,
    actor: str = "",
    team_slug: str | None = None,
    team_name: str | None = None,
    detail: str = "",
    verification_status: str = "unverified",
    source_system: str = "manual",
    source_ref: str | None = None,
    is_mock: bool = False,
    editable: bool = False,
    created_by: str = "system",
) -> TimelineEvent:
    if occurred_at is None:
        raise HTTPException(
            status_code=422,
            detail="occurred_at is required — timestamps are never fabricated",
        )
    if source_ref:
        existing = _find_by_source(db, incident.id, source_system, source_ref)
        if existing:
            # Refresh mutable fields from source of truth
            existing.event_type = event_type
            existing.occurred_at = occurred_at
            existing.actor = actor
            existing.team_slug = team_slug
            existing.team_name = team_name
            existing.detail = detail
            existing.verification_status = verification_status
            existing.is_mock = is_mock
            existing.updated_at = utc_now()
            db.commit()
            db.refresh(existing)
            return existing

    row = TimelineEvent(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        event_type=event_type,
        occurred_at=occurred_at,
        actor=actor,
        team_slug=team_slug,
        team_name=team_name,
        detail=detail,
        verification_status=verification_status,
        source_system=source_system,
        source_ref=source_ref,
        is_mock=is_mock,
        editable=editable,
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ensure_from_attendance(db: Session, att: BridgeAttendance) -> TimelineEvent:
    incident = db.query(Incident).filter(Incident.id == att.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    event_type = (
        "attendance_confirmed"
        if att.event_kind == "attendance_confirmed"
        else "teams_join"
    )
    return ensure_event(
        db,
        incident,
        event_type=event_type,
        occurred_at=att.joined_at,
        actor=att.display_name,
        team_slug=att.team_slug,
        team_name=att.team_name,
        detail=(
            f"{'MOCK SAMPLE · ' if att.is_mock else ''}"
            f"{event_type.replace('_', ' ')} on bridge #{att.bridge_id}"
            + (f" ({att.notes})" if att.notes else "")
        ),
        verification_status=att.verification_status,
        source_system="mock_sample" if att.is_mock else att.source,
        source_ref=f"attendance:{att.id}",
        is_mock=att.is_mock,
        editable=False,
        created_by=att.recorded_by,
    )


def rebuild_incident_timeline(db: Session, incident_id: int) -> list[TimelineEvent]:
    """Sync derived events from PD + bridges + attendance. Preserves manual edits."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    for pd in (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.incident_id == incident_id)
        .all()
    ):
        ensure_event(
            db,
            incident,
            event_type="pd_notify",
            occurred_at=pd.notified_at,
            actor=pd.team_name,
            team_slug=pd.team_slug,
            team_name=pd.team_name,
            detail=f"PagerDuty notified · {pd.pd_incident_id}",
            verification_status="verified",
            source_system="pagerduty",
            source_ref=f"pd_notify:{pd.id}",
            is_mock=pd.is_mock,
            editable=False,
            created_by="system",
        )
        if pd.acknowledged_at:
            ensure_event(
                db,
                incident,
                event_type="pd_ack",
                occurred_at=pd.acknowledged_at,
                actor=pd.team_name,
                team_slug=pd.team_slug,
                team_name=pd.team_name,
                detail=f"PagerDuty acknowledged · {pd.pd_incident_id}",
                verification_status="verified",
                source_system="pagerduty",
                source_ref=f"pd_ack:{pd.id}",
                is_mock=pd.is_mock,
                editable=False,
                created_by="system",
            )

    for bridge in (
        db.query(TeamsBridge).filter(TeamsBridge.incident_id == incident_id).all()
    ):
        ensure_event(
            db,
            incident,
            event_type="bridge_create",
            occurred_at=bridge.created_at,
            actor=bridge.created_by,
            detail=f"Bridge {bridge.bridge_code} created · {bridge.meeting_id}",
            verification_status="verified",
            source_system="teams",
            source_ref=f"bridge_create:{bridge.id}",
            is_mock=bridge.is_mock,
            editable=False,
            created_by="system",
        )
        if bridge.invited_at:
            ensure_event(
                db,
                incident,
                event_type="bridge_invite",
                occurred_at=bridge.invited_at,
                actor=bridge.created_by,
                detail=f"Responders invited to {bridge.bridge_code}",
                verification_status="verified",
                source_system="teams",
                source_ref=f"bridge_invite:{bridge.id}",
                is_mock=bridge.is_mock,
                editable=False,
                created_by="system",
            )
        if bridge.started_at:
            ensure_event(
                db,
                incident,
                event_type="bridge_open",
                occurred_at=bridge.started_at,
                actor=bridge.created_by,
                detail=f"Bridge {bridge.bridge_code} opened",
                verification_status="verified",
                source_system="teams",
                source_ref=f"bridge_open:{bridge.id}",
                is_mock=bridge.is_mock,
                editable=False,
                created_by="system",
            )
        if bridge.ended_at:
            ensure_event(
                db,
                incident,
                event_type="bridge_end",
                occurred_at=bridge.ended_at,
                actor=bridge.created_by,
                detail=f"Bridge {bridge.bridge_code} ended",
                verification_status="verified",
                source_system="teams",
                source_ref=f"bridge_end:{bridge.id}",
                is_mock=bridge.is_mock,
                editable=False,
                created_by="system",
            )

    for att in (
        db.query(BridgeAttendance)
        .filter(BridgeAttendance.incident_id == incident_id)
        .all()
    ):
        ensure_from_attendance(db, att)

    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.incident_id == incident_id)
        .order_by(TimelineEvent.occurred_at.asc(), TimelineEvent.id.asc())
        .all()
    )


def create_manual_event(
    db: Session,
    incident: Incident,
    *,
    occurred_at: datetime,
    detail: str,
    actor: str = "OCC Engineer",
    team_slug: str | None = None,
    team_name: str | None = None,
    verification_status: str = "unverified",
    is_mock: bool = False,
) -> TimelineEvent:
    if not detail.strip():
        raise HTTPException(status_code=422, detail="detail is required")
    if occurred_at is None:
        raise HTTPException(
            status_code=422,
            detail="occurred_at is required — timestamps are never fabricated",
        )
    row = ensure_event(
        db,
        incident,
        event_type="manual",
        occurred_at=occurred_at,
        actor=actor,
        team_slug=team_slug,
        team_name=team_name,
        detail=detail.strip(),
        verification_status=verification_status,
        source_system="manual",
        source_ref=None,
        is_mock=is_mock,
        editable=True,
        created_by=actor,
    )
    db.add(
        ApprovalAuditEvent(
            incident_id=incident.id,
            action=ApprovalAction.TIMELINE_CREATE.value,
            actor=actor,
            detail=f"Manual timeline entry: {detail[:120]}",
            approved_teams=incident.selected_team_slugs,
            severity=incident.working_severity,
        )
    )
    db.commit()
    db.refresh(row)
    return row


def edit_event(
    db: Session,
    event: TimelineEvent,
    *,
    actor: str,
    detail: str | None = None,
    occurred_at: datetime | None = None,
    verification_status: str | None = None,
    team_slug: str | None = None,
    team_name: str | None = None,
) -> TimelineEvent:
    if not event.editable:
        raise HTTPException(status_code=400, detail="This timeline event is not editable")
    before = _snapshot(event)
    if detail is not None:
        event.detail = detail.strip()
    if occurred_at is not None:
        event.occurred_at = occurred_at
    if verification_status is not None:
        event.verification_status = verification_status
    if team_slug is not None:
        event.team_slug = team_slug
    if team_name is not None:
        event.team_name = team_name
    event.verification_status = (
        verification_status if verification_status else "edited"
    )
    event.updated_at = utc_now()
    after = _snapshot(event)
    db.add(
        TimelineEventAudit(
            event_id=event.id,
            actor=actor,
            change_summary="Edited timeline entry",
            before_json=json.dumps(before),
            after_json=json.dumps(after),
        )
    )
    db.add(
        ApprovalAuditEvent(
            incident_id=event.incident_id,
            action=ApprovalAction.TIMELINE_EDIT.value,
            actor=actor,
            detail=f"Edited timeline event #{event.id}",
        )
    )
    db.commit()
    db.refresh(event)
    return event
