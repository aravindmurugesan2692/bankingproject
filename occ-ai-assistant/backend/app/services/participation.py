"""Bridge attendance + user→team mapping (Phase 6)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    ApprovalAction,
    ApprovalAuditEvent,
    BridgeAttendance,
    Incident,
    ResponderDirectory,
    TeamsBridge,
    utc_now,
)
from app.services import timeline as timeline_svc

# MOCK sample offsets from bridge.started_at — only used when bridge was opened.
# Clearly labeled is_mock / source=mock_sample; never used as silent fabrications.
MOCK_JOIN_OFFSETS_MINUTES = (2, 5, 9, 14)


def resolve_team_for_email(db: Session, email: str) -> tuple[str | None, str | None]:
    row = (
        db.query(ResponderDirectory)
        .filter(ResponderDirectory.email == email.lower().strip())
        .first()
    )
    if row:
        return row.team_slug, row.team_name
    return None, None


def resolve_team_for_name(db: Session, display_name: str) -> tuple[str | None, str | None]:
    row = (
        db.query(ResponderDirectory)
        .filter(ResponderDirectory.display_name == display_name.strip())
        .first()
    )
    if row:
        return row.team_slug, row.team_name
    return None, None


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


def record_attendance(
    db: Session,
    bridge: TeamsBridge,
    *,
    display_name: str,
    joined_at,
    email: str = "",
    team_slug: str | None = None,
    team_name: str | None = None,
    left_at=None,
    event_kind: str = "teams_join",
    source: str = "manual",
    verification_status: str = "unverified",
    is_mock: bool = False,
    notes: str | None = None,
    recorded_by: str = "OCC Engineer",
    sync_timeline: bool = True,
) -> BridgeAttendance:
    if not display_name.strip():
        raise HTTPException(status_code=422, detail="display_name is required")
    if joined_at is None:
        raise HTTPException(
            status_code=422,
            detail="joined_at is required — timestamps are never fabricated",
        )
    if event_kind not in {"teams_join", "attendance_confirmed"}:
        raise HTTPException(status_code=422, detail="Invalid event_kind")

    email_norm = (email or "").strip().lower()
    if not team_slug and email_norm:
        team_slug, team_name = resolve_team_for_email(db, email_norm)
    if not team_slug:
        mapped_slug, mapped_name = resolve_team_for_name(db, display_name)
        team_slug = team_slug or mapped_slug
        team_name = team_name or mapped_name

    row = BridgeAttendance(
        incident_id=bridge.incident_id,
        bridge_id=bridge.id,
        occ_incident_id=bridge.occ_incident_id,
        display_name=display_name.strip(),
        email=email_norm,
        team_slug=team_slug,
        team_name=team_name,
        event_kind=event_kind,
        joined_at=joined_at,
        left_at=left_at,
        source=source,
        verification_status=verification_status,
        is_mock=is_mock,
        notes=notes,
        recorded_by=recorded_by,
    )
    db.add(row)
    incident = db.query(Incident).filter(Incident.id == bridge.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.ATTENDANCE_RECORD.value,
            actor=recorded_by,
            detail=(
                f"{'MOCK SAMPLE ' if is_mock else ''}{event_kind}: "
                f"{display_name} joined {bridge.bridge_code} at {joined_at.isoformat()}"
            ),
        )
    db.commit()
    db.refresh(row)

    if sync_timeline and incident:
        timeline_svc.ensure_from_attendance(db, row)
    return row


def confirm_attendance(
    db: Session,
    row: BridgeAttendance,
    *,
    actor: str = "OCC Engineer",
) -> BridgeAttendance:
    row.event_kind = "attendance_confirmed"
    row.verification_status = "confirmed"
    row.updated_at = utc_now()
    incident = db.query(Incident).filter(Incident.id == row.incident_id).first()
    if incident:
        _audit(
            db,
            incident,
            action=ApprovalAction.ATTENDANCE_CONFIRM.value,
            actor=actor,
            detail=f"Confirmed attendance for {row.display_name}",
        )
    db.commit()
    db.refresh(row)
    timeline_svc.ensure_from_attendance(db, row)
    return row


def load_mock_sample_attendance(
    db: Session,
    bridge: TeamsBridge,
    *,
    actor: str = "OCC Engineer",
) -> list[BridgeAttendance]:
    """Load clearly labeled MOCK attendance samples.

    Requires bridge.started_at so join times are offsets from a real open action —
    not invented wall-clock fabrications.
    """
    if bridge.started_at is None:
        raise HTTPException(
            status_code=400,
            detail="Open the bridge first so MOCK join times can offset from started_at",
        )

    existing = (
        db.query(BridgeAttendance)
        .filter(BridgeAttendance.bridge_id == bridge.id)
        .count()
    )
    if existing:
        return (
            db.query(BridgeAttendance)
            .filter(BridgeAttendance.bridge_id == bridge.id)
            .order_by(BridgeAttendance.joined_at.asc())
            .all()
        )

    directory = (
        db.query(ResponderDirectory)
        .filter(ResponderDirectory.active.is_(True))
        .order_by(ResponderDirectory.id.asc())
        .limit(len(MOCK_JOIN_OFFSETS_MINUTES))
        .all()
    )
    if not directory:
        raise HTTPException(status_code=400, detail="Responder directory is empty")

    created: list[BridgeAttendance] = []
    for person, offset in zip(directory, MOCK_JOIN_OFFSETS_MINUTES, strict=False):
        joined = bridge.started_at + timedelta(minutes=offset)
        row = record_attendance(
            db,
            bridge,
            display_name=person.display_name,
            email=person.email,
            team_slug=person.team_slug,
            team_name=person.team_name,
            joined_at=joined,
            event_kind="teams_join",
            source="mock_sample",
            verification_status="unverified",
            is_mock=True,
            notes="MOCK SAMPLE attendance — labeled, offset from bridge started_at",
            recorded_by=actor,
            sync_timeline=True,
        )
        created.append(row)
    return created


async def sync_graph_attendance(
    db: Session,
    bridge: TeamsBridge,
    *,
    actor: str = "OCC Engineer",
) -> list[BridgeAttendance]:
    """Attempt Graph attendance reports; fall back to labeled MOCK samples."""
    settings = get_settings()
    if settings.use_live_teams and bridge.meeting_id and not bridge.is_mock:
        # Live Graph attendance reports require onlineMeeting advanced APIs /
        # organizer context. Until configured end-to-end, fall through to MOCK.
        pass
    return load_mock_sample_attendance(db, bridge, actor=actor)


def participation_matrix(db: Session, incident_id: int) -> list[dict[str, Any]]:
    """Per-person view distinguishing PD notify / PD ack / Teams join / confirmed."""
    from app.models import PagerDutyNotification

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    pd_rows = (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.incident_id == incident_id)
        .all()
    )
    attendance = (
        db.query(BridgeAttendance)
        .filter(BridgeAttendance.incident_id == incident_id)
        .order_by(BridgeAttendance.joined_at.asc())
        .all()
    )

    by_key: dict[str, dict[str, Any]] = {}

    def key_for(team_slug: str | None, name: str) -> str:
        return f"{team_slug or 'unknown'}::{name}"

    for pd in pd_rows:
        k = key_for(pd.team_slug, pd.team_name)
        entry = by_key.setdefault(
            k,
            {
                "display_name": pd.team_name,
                "email": "",
                "team_slug": pd.team_slug,
                "team_name": pd.team_name,
                "pd_notified": False,
                "pd_notified_at": None,
                "pd_acknowledged": False,
                "pd_acknowledged_at": None,
                "teams_joined": False,
                "teams_joined_at": None,
                "attendance_confirmed": False,
                "attendance_confirmed_at": None,
                "is_mock": pd.is_mock,
            },
        )
        entry["pd_notified"] = True
        entry["pd_notified_at"] = pd.notified_at
        if pd.acknowledged_at:
            entry["pd_acknowledged"] = True
            entry["pd_acknowledged_at"] = pd.acknowledged_at

    for att in attendance:
        k = key_for(att.team_slug, att.display_name)
        entry = by_key.setdefault(
            k,
            {
                "display_name": att.display_name,
                "email": att.email,
                "team_slug": att.team_slug,
                "team_name": att.team_name,
                "pd_notified": False,
                "pd_notified_at": None,
                "pd_acknowledged": False,
                "pd_acknowledged_at": None,
                "teams_joined": False,
                "teams_joined_at": None,
                "attendance_confirmed": False,
                "attendance_confirmed_at": None,
                "is_mock": att.is_mock,
            },
        )
        entry["display_name"] = att.display_name
        entry["email"] = att.email or entry["email"]
        entry["is_mock"] = entry["is_mock"] or att.is_mock
        if att.event_kind == "attendance_confirmed":
            entry["attendance_confirmed"] = True
            entry["attendance_confirmed_at"] = att.joined_at
            entry["teams_joined"] = True
            entry["teams_joined_at"] = entry["teams_joined_at"] or att.joined_at
        else:
            entry["teams_joined"] = True
            entry["teams_joined_at"] = att.joined_at

    return list(by_key.values())
