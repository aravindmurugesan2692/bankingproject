"""Team participation + bridge attendance APIs — Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BridgeAttendance, Incident, ResponderDirectory, TeamsBridge
from app.schemas import (
    AttendanceActorRequest,
    AttendanceCreateRequest,
    BridgeAttendanceRead,
    ParticipationRow,
    ResponderDirectoryRead,
)
from app.services import participation as part_svc

router = APIRouter(tags=["participation"])


@router.get("/responders", response_model=list[ResponderDirectoryRead])
def list_responders(db: Session = Depends(get_db)) -> list[ResponderDirectory]:
    return (
        db.query(ResponderDirectory)
        .filter(ResponderDirectory.active.is_(True))
        .order_by(ResponderDirectory.team_name.asc(), ResponderDirectory.display_name.asc())
        .all()
    )


@router.get(
    "/incidents/{incident_id}/participation",
    response_model=list[ParticipationRow],
)
def get_participation(
    incident_id: int, db: Session = Depends(get_db)
) -> list[ParticipationRow]:
    rows = part_svc.participation_matrix(db, incident_id)
    return [ParticipationRow(**r) for r in rows]


@router.get(
    "/incidents/{incident_id}/attendance",
    response_model=list[BridgeAttendanceRead],
)
def list_incident_attendance(
    incident_id: int, db: Session = Depends(get_db)
) -> list[BridgeAttendance]:
    if not db.query(Incident).filter(Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")
    return (
        db.query(BridgeAttendance)
        .filter(BridgeAttendance.incident_id == incident_id)
        .order_by(BridgeAttendance.joined_at.asc())
        .all()
    )


@router.get(
    "/bridges/{bridge_id}/attendance",
    response_model=list[BridgeAttendanceRead],
)
def list_bridge_attendance(
    bridge_id: int, db: Session = Depends(get_db)
) -> list[BridgeAttendance]:
    if not db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first():
        raise HTTPException(status_code=404, detail="Bridge not found")
    return (
        db.query(BridgeAttendance)
        .filter(BridgeAttendance.bridge_id == bridge_id)
        .order_by(BridgeAttendance.joined_at.asc())
        .all()
    )


@router.post(
    "/bridges/{bridge_id}/attendance",
    response_model=BridgeAttendanceRead,
)
def create_attendance(
    bridge_id: int,
    payload: AttendanceCreateRequest,
    db: Session = Depends(get_db),
) -> BridgeAttendance:
    bridge = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return part_svc.record_attendance(
        db,
        bridge,
        display_name=payload.display_name,
        email=payload.email,
        team_slug=payload.team_slug,
        team_name=payload.team_name,
        joined_at=payload.joined_at.replace(tzinfo=None)
        if payload.joined_at.tzinfo
        else payload.joined_at,
        left_at=(
            payload.left_at.replace(tzinfo=None)
            if payload.left_at and payload.left_at.tzinfo
            else payload.left_at
        ),
        event_kind=payload.event_kind,
        source="manual",
        verification_status="unverified",
        is_mock=False,
        notes=payload.notes,
        recorded_by=payload.actor,
    )


@router.post(
    "/bridges/{bridge_id}/attendance/sync",
    response_model=list[BridgeAttendanceRead],
)
async def sync_attendance(
    bridge_id: int,
    payload: AttendanceActorRequest,
    db: Session = Depends(get_db),
) -> list[BridgeAttendance]:
    bridge = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return await part_svc.sync_graph_attendance(db, bridge, actor=payload.actor)


@router.post(
    "/attendance/{attendance_id}/confirm",
    response_model=BridgeAttendanceRead,
)
def confirm_attendance(
    attendance_id: int,
    payload: AttendanceActorRequest,
    db: Session = Depends(get_db),
) -> BridgeAttendance:
    row = db.query(BridgeAttendance).filter(BridgeAttendance.id == attendance_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return part_svc.confirm_attendance(db, row, actor=payload.actor)
