"""ServiceNow work-note preview / approve / post with dedupe."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    BridgeAIUpdate,
    Incident,
    WorkNoteDraft,
    utc_now,
)


@dataclass
class PostResult:
    draft: WorkNoteDraft
    duplicate: bool
    is_mock: bool


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.strip().encode()).hexdigest()


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


def build_worknote_text(update: BridgeAIUpdate, incident: Incident) -> str:
    key_points = json.loads(update.key_points or "[]")
    questions = json.loads(update.open_questions or "[]")
    actions = json.loads(update.next_actions or "[]")
    hypotheses = json.loads(update.hypotheses or "[]")
    lines = [
        f"[OCC AI Bridge Assistant] {incident.occ_incident_id}",
        f"ServiceNow: {incident.servicenow_number or 'not linked'}",
        "",
        "=== Summary ===",
        update.summary,
        "",
        "=== Key points (from OCC-approved notes only) ===",
        *[f"- {p}" for p in key_points],
        "",
        "=== Hypotheses (UNCONFIRMED root cause) ===",
        *[f"- {h}" for h in hypotheses],
        "",
        "=== Open questions ===",
        *[f"- {q}" for q in questions],
        "",
        "=== Next actions ===",
        *[f"- {a}" for a in actions],
        "",
        f"Root cause status: {update.root_cause_status.upper()}",
        update.disclaimer,
        f"Source note ids: {update.source_note_ids}",
        f"Generator: {update.provider}/{update.model}"
        + (" (MOCK)" if update.is_mock else ""),
    ]
    return "\n".join(lines)


def preview_from_update(
    db: Session,
    incident: Incident,
    update: BridgeAIUpdate,
    *,
    actor: str = "OCC Engineer",
) -> WorkNoteDraft:
    if not incident.servicenow_sys_id:
        raise HTTPException(
            status_code=400,
            detail="Incident has no ServiceNow ticket — approve incident first",
        )
    content = build_worknote_text(update, incident)
    digest = _content_hash(content)

    existing_posted = (
        db.query(WorkNoteDraft)
        .filter(
            WorkNoteDraft.incident_id == incident.id,
            WorkNoteDraft.content_hash == digest,
            WorkNoteDraft.status.in_(["posted", "skipped_duplicate"]),
        )
        .first()
    )
    if existing_posted:
        # Return a new preview marked as would-be duplicate
        row = WorkNoteDraft(
            incident_id=incident.id,
            occ_incident_id=incident.occ_incident_id,
            bridge_update_id=update.id,
            content=content,
            content_hash=digest,
            status="preview",
            servicenow_number=incident.servicenow_number,
            servicenow_sys_id=incident.servicenow_sys_id,
            is_mock=bool(incident.servicenow_is_mock),
            created_by=actor,
        )
        db.add(row)
        _audit(
            db,
            incident,
            action=ApprovalAction.WORKNOTE_PREVIEW.value,
            actor=actor,
            detail=f"Work-note preview #{digest[:8]} (matches previously posted content)",
        )
        db.commit()
        db.refresh(row)
        return row

    row = WorkNoteDraft(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        bridge_update_id=update.id,
        content=content,
        content_hash=digest,
        status="preview",
        servicenow_number=incident.servicenow_number,
        servicenow_sys_id=incident.servicenow_sys_id,
        is_mock=bool(incident.servicenow_is_mock) or get_settings().mock_mode,
        created_by=actor,
    )
    db.add(row)
    _audit(
        db,
        incident,
        action=ApprovalAction.WORKNOTE_PREVIEW.value,
        actor=actor,
        detail=f"Work-note preview created ({digest[:12]})",
    )
    db.commit()
    db.refresh(row)
    return row


def approve_worknote(
    db: Session,
    draft: WorkNoteDraft,
    *,
    actor: str = "OCC Engineer",
) -> WorkNoteDraft:
    if draft.status in {"posted", "skipped_duplicate"}:
        return draft
    draft.status = "approved"
    draft.approved_by = actor
    draft.approved_at = utc_now()
    incident = db.query(Incident).filter(Incident.id == draft.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.WORKNOTE_APPROVE.value,
            actor=actor,
            detail=f"OCC approved work-note draft #{draft.id}",
        )
    db.commit()
    db.refresh(draft)
    return draft


async def post_worknote(
    db: Session,
    draft: WorkNoteDraft,
    *,
    actor: str = "OCC Engineer",
) -> PostResult:
    if draft.status == "preview":
        raise HTTPException(
            status_code=400,
            detail="OCC must approve the work-note preview before posting to ServiceNow",
        )
    if draft.status == "posted":
        return PostResult(draft=draft, duplicate=True, is_mock=draft.is_mock)
    if draft.status == "skipped_duplicate":
        return PostResult(draft=draft, duplicate=True, is_mock=draft.is_mock)
    if draft.status != "approved":
        raise HTTPException(status_code=400, detail=f"Cannot post from status {draft.status}")

    incident = db.query(Incident).filter(Incident.id == draft.incident_id).first()
    if not incident or not incident.servicenow_sys_id:
        raise HTTPException(status_code=400, detail="No ServiceNow sys_id on incident")

    # Dedupe: same hash already posted for this incident
    prior = (
        db.query(WorkNoteDraft)
        .filter(
            WorkNoteDraft.incident_id == draft.incident_id,
            WorkNoteDraft.content_hash == draft.content_hash,
            WorkNoteDraft.status == "posted",
            WorkNoteDraft.id != draft.id,
        )
        .first()
    )
    if prior:
        draft.status = "skipped_duplicate"
        draft.posted_at = utc_now()
        draft.posted_by = actor
        _audit(
            db,
            incident,
            action=ApprovalAction.WORKNOTE_SKIP_DUPLICATE.value,
            actor=actor,
            detail=f"Skipped duplicate work-note (matches draft #{prior.id})",
        )
        db.commit()
        db.refresh(draft)
        return PostResult(draft=draft, duplicate=True, is_mock=draft.is_mock)

    settings = get_settings()
    if not settings.use_live_servicenow:
        draft.status = "posted"
        draft.is_mock = True
        draft.posted_at = utc_now()
        draft.posted_by = actor
        _audit(
            db,
            incident,
            action=ApprovalAction.WORKNOTE_POST.value,
            actor=actor,
            detail=f"MOCK posted work-note to {incident.servicenow_number}",
        )
        db.commit()
        db.refresh(draft)
        return PostResult(draft=draft, duplicate=False, is_mock=True)

    await _live_post(incident, draft, settings)
    draft.status = "posted"
    draft.is_mock = False
    draft.posted_at = utc_now()
    draft.posted_by = actor
    _audit(
        db,
        incident,
        action=ApprovalAction.WORKNOTE_POST.value,
        actor=actor,
        detail=f"Posted work-note to {incident.servicenow_number}",
    )
    db.commit()
    db.refresh(draft)
    return PostResult(draft=draft, duplicate=False, is_mock=False)


async def _live_post(
    incident: Incident, draft: WorkNoteDraft, settings: Settings
) -> dict[str, Any]:
    base = settings.servicenow_instance_url.rstrip("/")
    url = f"{base}/api/now/table/incident/{incident.servicenow_sys_id}"
    auth = (settings.servicenow_username, settings.servicenow_password)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {"work_notes": draft.content}
    async with httpx.AsyncClient(timeout=settings.servicenow_timeout_seconds) as client:
        response = await client.patch(url, json=payload, auth=auth, headers=headers)
        response.raise_for_status()
        return response.json().get("result") or {}
