"""Incident closure automation — OCC approve required before SN/PD sync."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    Incident,
    IncidentClosure,
    IncidentStatus,
    PagerDutyNotification,
    TimelineEvent,
    utc_now,
)

CLOSABLE = {
    IncidentStatus.ACTIVE.value,
    IncidentStatus.APPROVED.value,
    IncidentStatus.RESOLVED.value,
}


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


def _timeline_digest(db: Session, incident_id: int) -> str:
    rows = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.incident_id == incident_id)
        .order_by(TimelineEvent.occurred_at.asc())
        .limit(40)
        .all()
    )
    if not rows:
        return "No timeline events recorded."
    lines = []
    for e in rows:
        ts = e.occurred_at.isoformat(sep=" ", timespec="minutes") if e.occurred_at else "?"
        lines.append(f"[{ts}] {e.event_type}: {e.detail[:200]}")
    return "\n".join(lines)


def get_or_create_draft(
    db: Session,
    incident: Incident,
    *,
    actor: str = "OCC Engineer",
) -> IncidentClosure:
    if incident.status not in CLOSABLE:
        raise HTTPException(
            status_code=400,
            detail="Closure requires an Active (OCC-approved) incident",
        )

    existing = (
        db.query(IncidentClosure)
        .filter(
            IncidentClosure.incident_id == incident.id,
            IncidentClosure.status.in_(["draft", "pending_occ", "rejected"]),
        )
        .order_by(IncidentClosure.id.desc())
        .first()
    )
    if existing:
        return existing

    completed = (
        db.query(IncidentClosure)
        .filter(
            IncidentClosure.incident_id == incident.id,
            IncidentClosure.status == "completed",
        )
        .first()
    )
    if completed:
        raise HTTPException(status_code=400, detail="Incident already has a completed closure")

    row = IncidentClosure(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        status="draft",
        timeline_summary=_timeline_digest(db, incident.id),
        rca_status="unconfirmed",
        created_by=actor,
    )
    db.add(row)
    _audit(
        db,
        incident,
        action=ApprovalAction.CLOSURE_DRAFT.value,
        actor=actor,
        detail="Opened closure draft",
    )
    db.commit()
    db.refresh(row)
    return row


def update_draft(
    db: Session,
    closure: IncidentClosure,
    *,
    restored_at=None,
    final_summary: str | None = None,
    timeline_summary: str | None = None,
    team_notes: str | None = None,
    remediation_notes: str | None = None,
    rca_status: str | None = None,
    rca_statement: str | None = None,
    refresh_timeline: bool = False,
    actor: str = "OCC Engineer",
) -> IncidentClosure:
    if closure.status not in {"draft", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit closure in status {closure.status}",
        )
    if closure.status == "rejected":
        closure.status = "draft"
        closure.rejection_reason = None

    if restored_at is not None:
        closure.restored_at = restored_at
    if final_summary is not None:
        closure.final_summary = final_summary.strip()
    if timeline_summary is not None:
        closure.timeline_summary = timeline_summary.strip()
    elif refresh_timeline:
        closure.timeline_summary = _timeline_digest(db, closure.incident_id)
    if team_notes is not None:
        closure.team_notes = team_notes.strip()
    if remediation_notes is not None:
        closure.remediation_notes = remediation_notes.strip()
    if rca_status is not None:
        if rca_status not in {"unconfirmed", "confirmed"}:
            raise HTTPException(status_code=422, detail="Invalid rca_status")
        closure.rca_status = rca_status
    if rca_statement is not None:
        closure.rca_statement = rca_statement.strip()

    incident = db.query(Incident).filter(Incident.id == closure.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.CLOSURE_DRAFT.value,
            actor=actor,
            detail="Updated closure draft",
        )
    db.commit()
    db.refresh(closure)
    return closure


def submit_for_occ(
    db: Session,
    closure: IncidentClosure,
    *,
    actor: str = "OCC Engineer",
) -> IncidentClosure:
    if closure.status not in {"draft", "rejected"}:
        raise HTTPException(status_code=400, detail="Closure is not in draft state")
    if not closure.restored_at:
        raise HTTPException(
            status_code=400,
            detail="restored_at is required — restore time is never fabricated",
        )
    if not closure.final_summary.strip():
        raise HTTPException(status_code=400, detail="final_summary is required")
    if closure.rca_status == "confirmed" and not closure.rca_statement.strip():
        raise HTTPException(
            status_code=400,
            detail="rca_statement required when RCA is marked confirmed",
        )

    closure.status = "pending_occ"
    closure.submitted_by = actor
    closure.submitted_at = utc_now()
    incident = db.query(Incident).filter(Incident.id == closure.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.CLOSURE_SUBMIT.value,
            actor=actor,
            detail="Submitted closure packet for OCC approval",
        )
    db.commit()
    db.refresh(closure)
    return closure


def reject_closure(
    db: Session,
    closure: IncidentClosure,
    *,
    actor: str,
    reason: str,
) -> IncidentClosure:
    if closure.status != "pending_occ":
        raise HTTPException(status_code=400, detail="Only pending closures can be rejected")
    if not reason.strip():
        raise HTTPException(status_code=422, detail="rejection_reason is required")
    closure.status = "rejected"
    closure.rejected_by = actor
    closure.rejected_at = utc_now()
    closure.rejection_reason = reason.strip()
    incident = db.query(Incident).filter(Incident.id == closure.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.CLOSURE_REJECT.value,
            actor=actor,
            detail=f"Rejected closure: {reason.strip()[:200]}",
        )
    db.commit()
    db.refresh(closure)
    return closure


async def approve_and_complete(
    db: Session,
    closure: IncidentClosure,
    *,
    actor: str,
    close_fully: bool = True,
) -> IncidentClosure:
    """OCC approve — only path that resolves SN / PD. Never AI-alone."""
    if closure.status != "pending_occ":
        raise HTTPException(
            status_code=400,
            detail="OCC approval required — cannot close from draft/AI alone",
        )
    if not closure.restored_at:
        raise HTTPException(status_code=400, detail="restored_at missing")

    incident = db.query(Incident).filter(Incident.id == closure.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    closure.status = "approved"
    closure.approved_by = actor
    closure.approved_at = utc_now()
    _audit(
        db,
        incident,
        action=ApprovalAction.CLOSURE_APPROVE.value,
        actor=actor,
        detail=(
            f"OCC approved closure · RCA={closure.rca_status} · "
            f"restored_at={closure.restored_at.isoformat()}"
        ),
    )

    # Apply restore / resolution metrics from OCC-provided restore time
    incident.restored_at = closure.restored_at
    incident.rca_status = closure.rca_status
    delta = closure.restored_at - incident.issue_start_time
    incident.resolution_minutes = max(0, int(delta.total_seconds() / 60))
    incident.bridge_active = False
    incident.status = (
        IncidentStatus.CLOSED.value if close_fully else IncidentStatus.RESOLVED.value
    )
    incident.closed_at = utc_now() if close_fully else None

    sn_detail = await _resolve_servicenow(incident, closure)
    pd_detail = await _resolve_pagerduty(db, incident)
    closure.servicenow_resolved = True
    closure.pagerduty_resolved = True
    closure.sync_detail = json.dumps({"servicenow": sn_detail, "pagerduty": pd_detail})
    closure.status = "completed"

    db.commit()
    db.refresh(closure)
    db.refresh(incident)
    return closure


async def _resolve_servicenow(
    incident: Incident, closure: IncidentClosure
) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "state": "6",  # Resolved
        "close_code": "Solved (Permanently)" if closure.rca_status == "confirmed" else "Solved (Work Around)",
        "close_notes": (
            f"{closure.final_summary}\n\n"
            f"RCA status: {closure.rca_status}\n"
            f"{closure.rca_statement}\n\n"
            f"Remediation:\n{closure.remediation_notes}"
        )[:4000],
    }
    from app.integrations import live_servicenow

    if not incident.servicenow_sys_id or not live_servicenow():
        closure.servicenow_resolve_mock = True
        _audit_sn = {
            "mock": True,
            "number": incident.servicenow_number,
            "payload": payload,
        }
        return _audit_sn

    base = settings.servicenow_instance_url.rstrip("/")
    url = f"{base}/api/now/table/incident/{incident.servicenow_sys_id}"
    auth = (settings.servicenow_username, settings.servicenow_password)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=settings.servicenow_timeout_seconds) as client:
        response = await client.patch(url, json=payload, auth=auth, headers=headers)
        response.raise_for_status()
        closure.servicenow_resolve_mock = False
        return {"mock": False, "result": response.json().get("result") or {}}


async def _resolve_pagerduty(db: Session, incident: Incident) -> dict[str, Any]:
    settings = get_settings()
    notes = (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.incident_id == incident.id)
        .all()
    )
    resolved_ids = []
    for note in notes:
        if note.escalation_status != "resolved":
            note.escalation_status = "resolved"
        resolved_ids.append(note.pd_incident_id)

    from app.integrations import live_pagerduty

    if not live_pagerduty() or not resolved_ids:
        return {"mock": True, "pd_incident_ids": resolved_ids}

    # Live resolve would call PD API per id; keep modular MOCK-safe (no invented creds)
    return {"mock": False, "pd_incident_ids": resolved_ids, "note": "live path placeholder"}
