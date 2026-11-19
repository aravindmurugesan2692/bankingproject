"""Teams Bridge Management APIs — Phase 5."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, TeamsBridge
from app.schemas import (
    BridgeActorRequest,
    BridgeCreateRequest,
    BridgeInviteRequest,
    TeamsBridgeRead,
)
from app.services import bridges as bridge_svc

router = APIRouter(prefix="/bridges", tags=["bridges"])


def _serialize(row: TeamsBridge) -> TeamsBridgeRead:
    invited: list[dict] = []
    if row.invited_responders:
        try:
            parsed = json.loads(row.invited_responders)
            if isinstance(parsed, list):
                invited = [x for x in parsed if isinstance(x, dict)]
        except json.JSONDecodeError:
            invited = []
    return TeamsBridgeRead(
        id=row.id,
        incident_id=row.incident_id,
        occ_incident_id=row.occ_incident_id,
        servicenow_number=row.servicenow_number,
        bridge_code=row.bridge_code,
        title=row.title,
        provider=row.provider,
        meeting_id=row.meeting_id,
        meeting_url=row.meeting_url,
        status=row.status,
        created_at=row.created_at,
        started_at=row.started_at,
        ended_at=row.ended_at,
        invited_responders=invited,
        invited_count=len(invited),
        invited_at=row.invited_at,
        is_mock=row.is_mock,
        created_by=row.created_by,
    )


@router.get("", response_model=list[TeamsBridgeRead])
def list_bridges(db: Session = Depends(get_db)) -> list[TeamsBridgeRead]:
    rows = db.query(TeamsBridge).order_by(TeamsBridge.created_at.desc()).all()
    return [_serialize(r) for r in rows]


@router.get("/{bridge_id}", response_model=TeamsBridgeRead)
def get_bridge(bridge_id: int, db: Session = Depends(get_db)) -> TeamsBridgeRead:
    row = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return _serialize(row)


@router.get("/by-incident/{incident_id}", response_model=list[TeamsBridgeRead])
def list_incident_bridges(
    incident_id: int, db: Session = Depends(get_db)
) -> list[TeamsBridgeRead]:
    rows = (
        db.query(TeamsBridge)
        .filter(TeamsBridge.incident_id == incident_id)
        .order_by(TeamsBridge.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


@router.post("", response_model=TeamsBridgeRead)
async def create_bridge(
    payload: BridgeCreateRequest, db: Session = Depends(get_db)
) -> TeamsBridgeRead:
    if not payload.incident_id:
        raise HTTPException(status_code=422, detail="incident_id is required")
    incident = db.query(Incident).filter(Incident.id == payload.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    row = await bridge_svc.create_bridge(
        db,
        incident,
        actor=payload.actor,
        bridge_code=payload.bridge_code,
        invite=payload.invite,
    )
    return _serialize(row)


@router.post("/incidents/{incident_id}", response_model=TeamsBridgeRead)
async def create_bridge_for_incident(
    incident_id: int,
    payload: BridgeCreateRequest,
    db: Session = Depends(get_db),
) -> TeamsBridgeRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    row = await bridge_svc.create_bridge(
        db,
        incident,
        actor=payload.actor,
        bridge_code=payload.bridge_code,
        invite=payload.invite,
    )
    return _serialize(row)


@router.post("/{bridge_id}/open", response_model=TeamsBridgeRead)
def open_bridge(
    bridge_id: int,
    payload: BridgeActorRequest,
    db: Session = Depends(get_db),
) -> TeamsBridgeRead:
    row = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return _serialize(bridge_svc.open_bridge(db, row, actor=payload.actor))


@router.post("/{bridge_id}/end", response_model=TeamsBridgeRead)
def end_bridge(
    bridge_id: int,
    payload: BridgeActorRequest,
    db: Session = Depends(get_db),
) -> TeamsBridgeRead:
    row = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return _serialize(bridge_svc.end_bridge(db, row, actor=payload.actor))


@router.post("/{bridge_id}/invite", response_model=TeamsBridgeRead)
async def invite_bridge(
    bridge_id: int,
    payload: BridgeInviteRequest,
    db: Session = Depends(get_db),
) -> TeamsBridgeRead:
    row = db.query(TeamsBridge).filter(TeamsBridge.id == bridge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bridge not found")
    updated = await bridge_svc.invite_to_bridge(
        db, row, actor=payload.actor, responders=payload.responders
    )
    return _serialize(updated)
