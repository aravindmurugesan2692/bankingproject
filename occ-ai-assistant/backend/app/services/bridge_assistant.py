"""AI Bridge Assistant — structured updates from OCC-approved notes only."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    BridgeAIUpdate,
    BridgeNote,
    Incident,
    utc_now,
)

DISCLAIMER = (
    "AI Bridge Assistant output is a structured hypothesis for OCC review — "
    "NOT confirmed root cause. Do not treat findings as verified without OCC validation."
)


def _audit(
    db: Session,
    incident: Incident,
    *,
    action: str,
    actor: str,
    detail: str,
) -> None:
    db.add(
        ApprovalAuditEvent(
            incident_id=incident.id,
            action=action,
            actor=actor,
            detail=detail,
            approved_teams=incident.selected_team_slugs,
            severity=incident.working_severity,
        )
    )


def add_bridge_note(
    db: Session,
    incident: Incident,
    *,
    content: str,
    title: str = "",
    note_type: str = "manual",
    occurred_at=None,
    bridge_id: int | None = None,
    approve_now: bool = False,
    actor: str = "OCC Engineer",
    is_mock: bool = False,
) -> BridgeNote:
    if not content.strip():
        raise HTTPException(status_code=422, detail="content is required")
    if note_type not in {"manual", "transcript_excerpt"}:
        raise HTTPException(status_code=422, detail="Invalid note_type")

    row = BridgeNote(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        bridge_id=bridge_id,
        note_type=note_type,
        title=(title or "").strip()[:255],
        content=content.strip(),
        occurred_at=occurred_at,
        status="approved" if approve_now else "draft",
        approved_by=actor if approve_now else None,
        approved_at=utc_now() if approve_now else None,
        is_mock=is_mock,
        created_by=actor,
    )
    db.add(row)
    _audit(
        db,
        incident,
        action=ApprovalAction.BRIDGE_NOTE_ADD.value,
        actor=actor,
        detail=f"Added {note_type} bridge note ({'approved' if approve_now else 'draft'})",
    )
    if approve_now:
        _audit(
            db,
            incident,
            action=ApprovalAction.BRIDGE_NOTE_APPROVE.value,
            actor=actor,
            detail="Approved bridge note on create",
        )
    db.commit()
    db.refresh(row)
    return row


def approve_bridge_note(
    db: Session,
    note: BridgeNote,
    *,
    actor: str = "OCC Engineer",
) -> BridgeNote:
    if note.status == "approved":
        return note
    note.status = "approved"
    note.approved_by = actor
    note.approved_at = utc_now()
    incident = db.query(Incident).filter(Incident.id == note.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.BRIDGE_NOTE_APPROVE.value,
            actor=actor,
            detail=f"Approved bridge note #{note.id}",
        )
    db.commit()
    db.refresh(note)
    return note


def _heuristic_update(notes: list[BridgeNote], incident: Incident) -> dict[str, Any]:
    """Derive structured fields only from provided note text — no invented activities."""
    blobs = [n.content.strip() for n in notes if n.content.strip()]
    combined = "\n\n".join(blobs)
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", combined)
        if s.strip()
    ]
    key_points = sentences[:5] if sentences else ["No extractable statements in approved notes."]
    questions = [
        s
        for s in sentences
        if "?" in s or s.lower().startswith(("what ", "why ", "how ", "who "))
    ][:4]
    if not questions:
        questions = [
            "What additional evidence is needed to confirm or reject current hypotheses?"
        ]

    actions: list[str] = []
    for s in sentences:
        low = s.lower()
        if any(
            k in low
            for k in ("will ", "next ", "plan ", "follow", "check", "verify", "rollback")
        ):
            actions.append(s)
    if not actions:
        actions = ["OCC to validate AI hypotheses against monitoring before further action."]

    hypotheses: list[str] = []
    for s in sentences:
        low = s.lower()
        if any(k in low for k in ("suspect", "possible", "might", "could be", "hypothesis", "likely")):
            hypotheses.append(s)
    if not hypotheses:
        hypotheses = [
            "Insufficient confirmed evidence in approved notes to assert a root cause."
        ]

    summary = (
        f"Structured bridge update for {incident.occ_incident_id} based on "
        f"{len(notes)} OCC-approved note(s). "
        + (sentences[0] if sentences else "No narrative content available.")
    )
    return {
        "summary": summary[:2000],
        "key_points": key_points,
        "open_questions": questions,
        "next_actions": actions[:5],
        "hypotheses": hypotheses[:5],
        "root_cause_status": "unconfirmed",
        "disclaimer": DISCLAIMER,
    }


async def _llm_update(
    notes: list[BridgeNote], incident: Incident, settings: Settings
) -> dict[str, Any] | None:
    if not settings.use_live_llm:
        return None
    note_blocks = "\n\n".join(
        f"[{n.note_type}#{n.id} @ {n.occurred_at or n.created_at}]\n{n.content}"
        for n in notes
    )
    prompt = (
        "You are an OCC bridge assistant. Use ONLY the approved notes below. "
        "Do not invent activities, attendees, or timestamps not present in the notes. "
        "Mark root cause as unconfirmed. Return ONLY JSON with keys: "
        "summary, key_points, open_questions, next_actions, hypotheses, "
        "root_cause_status (unconfirmed|insufficient_evidence).\n\n"
        f"Incident: {incident.occ_incident_id} — {incident.title}\n\n"
        f"Approved notes:\n{note_blocks}"
    )
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key.strip()}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            parsed = json.loads(match.group(0))
            parsed["disclaimer"] = DISCLAIMER
            parsed.setdefault("root_cause_status", "unconfirmed")
            return parsed
    except Exception:  # noqa: BLE001
        return None


async def generate_bridge_update(
    db: Session,
    incident: Incident,
    *,
    note_ids: list[int] | None = None,
    actor: str = "OCC Engineer",
) -> BridgeAIUpdate:
    query = db.query(BridgeNote).filter(
        BridgeNote.incident_id == incident.id,
        BridgeNote.status == "approved",
    )
    if note_ids:
        query = query.filter(BridgeNote.id.in_(note_ids))
    notes = query.order_by(BridgeNote.created_at.asc()).all()
    if not notes:
        raise HTTPException(
            status_code=400,
            detail="No OCC-approved bridge notes/transcripts available for AI assistant",
        )

    settings = get_settings()
    payload = await _llm_update(notes, incident, settings)
    provider = "llm" if payload else "heuristic"
    model = settings.llm_model if payload else "mock-bridge-assistant-v1"
    is_mock = payload is None or settings.mock_mode
    if payload is None:
        payload = _heuristic_update(notes, incident)

    row = BridgeAIUpdate(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        summary=str(payload.get("summary") or ""),
        key_points=json.dumps(payload.get("key_points") or []),
        open_questions=json.dumps(payload.get("open_questions") or []),
        next_actions=json.dumps(payload.get("next_actions") or []),
        hypotheses=json.dumps(payload.get("hypotheses") or []),
        source_note_ids=json.dumps([n.id for n in notes]),
        root_cause_status=str(payload.get("root_cause_status") or "unconfirmed"),
        disclaimer=str(payload.get("disclaimer") or DISCLAIMER),
        provider=provider,
        model=model,
        is_mock=is_mock,
        raw_json=json.dumps(payload),
        created_by=actor,
    )
    db.add(row)
    _audit(
        db,
        incident,
        action=ApprovalAction.BRIDGE_AI_GENERATE.value,
        actor=actor,
        detail=(
            f"{'MOCK ' if is_mock else ''}AI bridge update from "
            f"{len(notes)} approved note(s); root_cause={row.root_cause_status}"
        ),
    )
    db.commit()
    db.refresh(row)
    return row
