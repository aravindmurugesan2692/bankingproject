"""OCC Teams bridge orchestration — create / open / invite / end."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    Incident,
    IncidentStatus,
    SupportTeam,
    TeamsBridge,
    utc_now,
)
from app.services.conferencing import get_conferencing_provider

BRIDGE_ELIGIBLE = {
    IncidentStatus.APPROVED.value,
    IncidentStatus.ACTIVE.value,
}

BRIDGE_CODES = ("STS1", "STS2", "STS3", "STS4")


def _next_bridge_code(db: Session) -> str:
    openish = (
        db.query(TeamsBridge)
        .filter(TeamsBridge.status.in_(["created", "open"]))
        .all()
    )
    used = {b.bridge_code for b in openish}
    for code in BRIDGE_CODES:
        if code not in used:
            return code
    # Allow overflow codes rather than blocking OCC
    return f"STS{len(openish) + 1}"


def _slug_list(incident: Incident) -> list[str]:
    if not incident.selected_team_slugs:
        return []
    try:
        parsed = json.loads(incident.selected_team_slugs)
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _responders_for_incident(db: Session, incident: Incident) -> list[dict[str, Any]]:
    slugs = _slug_list(incident)
    if not slugs:
        return []
    teams = (
        db.query(SupportTeam)
        .filter(SupportTeam.slug.in_(slugs), SupportTeam.active.is_(True))
        .all()
    )
    by_slug = {t.slug: t for t in teams}
    out: list[dict[str, Any]] = []
    for slug in slugs:
        team = by_slug.get(slug)
        if not team:
            continue
        out.append(
            {
                "name": team.name,
                "team_slug": team.slug,
                "email": f"{team.slug}@responders.example.local",
            }
        )
    return out


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


async def create_bridge(
    db: Session,
    incident: Incident,
    *,
    actor: str = "OCC Engineer",
    bridge_code: str | None = None,
    invite: bool = True,
) -> TeamsBridge:
    if incident.status not in BRIDGE_ELIGIBLE:
        raise HTTPException(
            status_code=400,
            detail="Bridge requires an OCC-approved (or Active) incident",
        )

    existing_open = (
        db.query(TeamsBridge)
        .filter(
            TeamsBridge.incident_id == incident.id,
            TeamsBridge.status.in_(["created", "open"]),
        )
        .first()
    )
    if existing_open:
        return existing_open

    code = (bridge_code or "").strip().upper() or _next_bridge_code(db)
    provider = get_conferencing_provider()
    meeting = await provider.create_meeting(
        title=incident.title,
        bridge_code=code,
        occ_incident_id=incident.occ_incident_id,
        description=incident.working_description or incident.description,
    )

    row = TeamsBridge(
        incident_id=incident.id,
        occ_incident_id=incident.occ_incident_id,
        servicenow_number=incident.servicenow_number,
        bridge_code=code,
        title=incident.title,
        provider=meeting.provider,
        meeting_id=meeting.meeting_id,
        meeting_url=meeting.meeting_url,
        status="created",
        # started_at / ended_at intentionally null until open / end
        is_mock=meeting.is_mock,
        raw_json=json.dumps(meeting.raw) if meeting.raw else None,
        created_by=actor,
    )
    db.add(row)
    incident.bridge_active = True
    _audit(
        db,
        incident,
        action=ApprovalAction.BRIDGE_CREATE.value,
        actor=actor,
        detail=(
            f"{'MOCK ' if meeting.is_mock else ''}Bridge {code} "
            f"meeting {meeting.meeting_id}"
        ),
    )
    db.commit()
    db.refresh(row)

    if invite:
        row = await invite_to_bridge(db, row, actor=actor)
    return row


async def invite_to_bridge(
    db: Session,
    bridge: TeamsBridge,
    *,
    actor: str = "OCC Engineer",
    responders: list[dict[str, Any]] | None = None,
) -> TeamsBridge:
    if bridge.status == "ended":
        raise HTTPException(status_code=400, detail="Cannot invite to an ended bridge")

    incident = db.query(Incident).filter(Incident.id == bridge.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    people = responders if responders is not None else _responders_for_incident(db, incident)
    provider = get_conferencing_provider()
    result = await provider.invite_responders(
        meeting_id=bridge.meeting_id,
        meeting_url=bridge.meeting_url,
        responders=people,
    )
    bridge.invited_responders = json.dumps(result.invited)
    bridge.invited_at = utc_now()  # set only when invite action runs
    _audit(
        db,
        incident,
        action=ApprovalAction.BRIDGE_INVITE.value,
        actor=actor,
        detail=f"Invited {len(result.invited)} responder(s) to {bridge.bridge_code}",
    )
    db.commit()
    db.refresh(bridge)
    return bridge


def open_bridge(
    db: Session,
    bridge: TeamsBridge,
    *,
    actor: str = "OCC Engineer",
) -> TeamsBridge:
    if bridge.status == "ended":
        raise HTTPException(status_code=400, detail="Cannot open an ended bridge")
    if bridge.status != "open":
        bridge.status = "open"
        if bridge.started_at is None:
            bridge.started_at = utc_now()  # real open time only
        incident = db.query(Incident).filter(Incident.id == bridge.incident_id).first()
        if incident:
            incident.bridge_active = True
            _audit(
                db,
                incident,
                action=ApprovalAction.BRIDGE_OPEN.value,
                actor=actor,
                detail=f"Opened bridge {bridge.bridge_code}",
            )
        db.commit()
        db.refresh(bridge)
    return bridge


def end_bridge(
    db: Session,
    bridge: TeamsBridge,
    *,
    actor: str = "OCC Engineer",
) -> TeamsBridge:
    if bridge.status == "ended":
        return bridge
    bridge.status = "ended"
    bridge.ended_at = utc_now()  # real end time only
    incident = db.query(Incident).filter(Incident.id == bridge.incident_id).first()
    if incident:
        other_open = (
            db.query(TeamsBridge)
            .filter(
                TeamsBridge.incident_id == incident.id,
                TeamsBridge.id != bridge.id,
                TeamsBridge.status.in_(["created", "open"]),
            )
            .count()
        )
        if other_open == 0:
            incident.bridge_active = False
        _audit(
            db,
            incident,
            action=ApprovalAction.BRIDGE_END.value,
            actor=actor,
            detail=f"Ended bridge {bridge.bridge_code}",
        )
    db.commit()
    db.refresh(bridge)
    return bridge


def invited_count(bridge: TeamsBridge) -> int:
    if not bridge.invited_responders:
        return 0
    try:
        parsed = json.loads(bridge.invited_responders)
        return len(parsed) if isinstance(parsed, list) else 0
    except json.JSONDecodeError:
        return 0
