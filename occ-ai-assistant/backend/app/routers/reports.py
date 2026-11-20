"""AI Bridge Assistant + ServiceNow work notes — Phase 7."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BridgeAIUpdate, BridgeNote, Incident, WorkNoteDraft
from app.schemas import (
    BridgeAIGenerateRequest,
    BridgeAIUpdateRead,
    BridgeNoteActorRequest,
    BridgeNoteCreateRequest,
    BridgeNoteRead,
    WorkNoteActorRequest,
    WorkNoteDraftRead,
    WorkNotePostResponse,
)
from app.services import bridge_assistant as assist
from app.services import worknotes as wn

router = APIRouter(tags=["reports"])


def _serialize_update(row: BridgeAIUpdate) -> BridgeAIUpdateRead:
    def _list(raw: str) -> list:
        try:
            parsed = json.loads(raw or "[]")
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    ids = _list(row.source_note_ids)
    return BridgeAIUpdateRead(
        id=row.id,
        incident_id=row.incident_id,
        occ_incident_id=row.occ_incident_id,
        summary=row.summary,
        key_points=[str(x) for x in _list(row.key_points)],
        open_questions=[str(x) for x in _list(row.open_questions)],
        next_actions=[str(x) for x in _list(row.next_actions)],
        hypotheses=[str(x) for x in _list(row.hypotheses)],
        source_note_ids=[int(x) for x in ids if str(x).isdigit() or isinstance(x, int)],
        root_cause_status=row.root_cause_status,
        disclaimer=row.disclaimer,
        provider=row.provider,
        model=row.model,
        is_mock=row.is_mock,
        created_by=row.created_by,
        created_at=row.created_at,
    )


@router.get("/incidents/{incident_id}/bridge-notes", response_model=list[BridgeNoteRead])
def list_notes(incident_id: int, db: Session = Depends(get_db)) -> list[BridgeNote]:
    if not db.query(Incident).filter(Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")
    return (
        db.query(BridgeNote)
        .filter(BridgeNote.incident_id == incident_id)
        .order_by(BridgeNote.created_at.desc())
        .all()
    )


@router.post("/incidents/{incident_id}/bridge-notes", response_model=BridgeNoteRead)
def create_note(
    incident_id: int,
    payload: BridgeNoteCreateRequest,
    db: Session = Depends(get_db),
) -> BridgeNote:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    occurred = None
    if payload.occurred_at is not None:
        occurred = (
            payload.occurred_at.replace(tzinfo=None)
            if payload.occurred_at.tzinfo
            else payload.occurred_at
        )
    return assist.add_bridge_note(
        db,
        incident,
        content=payload.content,
        title=payload.title,
        note_type=payload.note_type,
        occurred_at=occurred,
        bridge_id=payload.bridge_id,
        approve_now=payload.approve_now,
        actor=payload.actor,
        is_mock=payload.is_mock,
    )


@router.post("/bridge-notes/{note_id}/approve", response_model=BridgeNoteRead)
def approve_note(
    note_id: int,
    payload: BridgeNoteActorRequest,
    db: Session = Depends(get_db),
) -> BridgeNote:
    note = db.query(BridgeNote).filter(BridgeNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Bridge note not found")
    return assist.approve_bridge_note(db, note, actor=payload.actor)


@router.get(
    "/incidents/{incident_id}/bridge-updates",
    response_model=list[BridgeAIUpdateRead],
)
def list_updates(
    incident_id: int, db: Session = Depends(get_db)
) -> list[BridgeAIUpdateRead]:
    if not db.query(Incident).filter(Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")
    rows = (
        db.query(BridgeAIUpdate)
        .filter(BridgeAIUpdate.incident_id == incident_id)
        .order_by(BridgeAIUpdate.created_at.desc())
        .all()
    )
    return [_serialize_update(r) for r in rows]


@router.post(
    "/incidents/{incident_id}/bridge-updates/generate",
    response_model=BridgeAIUpdateRead,
)
async def generate_update(
    incident_id: int,
    payload: BridgeAIGenerateRequest,
    db: Session = Depends(get_db),
) -> BridgeAIUpdateRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    row = await assist.generate_bridge_update(
        db, incident, note_ids=payload.note_ids, actor=payload.actor
    )
    return _serialize_update(row)


@router.get("/incidents/{incident_id}/work-notes", response_model=list[WorkNoteDraftRead])
def list_worknotes(
    incident_id: int, db: Session = Depends(get_db)
) -> list[WorkNoteDraft]:
    if not db.query(Incident).filter(Incident.id == incident_id).first():
        raise HTTPException(status_code=404, detail="Incident not found")
    return (
        db.query(WorkNoteDraft)
        .filter(WorkNoteDraft.incident_id == incident_id)
        .order_by(WorkNoteDraft.created_at.desc())
        .all()
    )


@router.post(
    "/bridge-updates/{update_id}/work-notes/preview",
    response_model=WorkNoteDraftRead,
)
def preview_worknote(
    update_id: int,
    payload: WorkNoteActorRequest,
    db: Session = Depends(get_db),
) -> WorkNoteDraft:
    update = db.query(BridgeAIUpdate).filter(BridgeAIUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Bridge AI update not found")
    incident = db.query(Incident).filter(Incident.id == update.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return wn.preview_from_update(db, incident, update, actor=payload.actor)


@router.post("/work-notes/{draft_id}/approve", response_model=WorkNoteDraftRead)
def approve_worknote(
    draft_id: int,
    payload: WorkNoteActorRequest,
    db: Session = Depends(get_db),
) -> WorkNoteDraft:
    draft = db.query(WorkNoteDraft).filter(WorkNoteDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Work-note draft not found")
    return wn.approve_worknote(db, draft, actor=payload.actor)


@router.post("/work-notes/{draft_id}/post", response_model=WorkNotePostResponse)
async def post_worknote(
    draft_id: int,
    payload: WorkNoteActorRequest,
    db: Session = Depends(get_db),
) -> WorkNotePostResponse:
    draft = db.query(WorkNoteDraft).filter(WorkNoteDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Work-note draft not found")
    result = await wn.post_worknote(db, draft, actor=payload.actor)
    return WorkNotePostResponse(
        draft=WorkNoteDraftRead.model_validate(result.draft),
        duplicate=result.duplicate,
        is_mock=result.is_mock,
    )
