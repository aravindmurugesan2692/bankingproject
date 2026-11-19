"""Dashboard summary and mock-labeled aggregates."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import (
    Incident,
    IncidentPriority,
    IncidentStatus,
    PagerDutyNotification,
    TeamsBridge,
)
from app.schemas import (
    DashboardBundle,
    DashboardSummary,
    IncidentRead,
    PagerDutyNotificationRead,
    TeamsBridgeRead,
)
from app.services.bridges import invited_count

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

ACTIVE_STATUSES = {
    IncidentStatus.NEW.value,
    IncidentStatus.ANALYZED.value,
    IncidentStatus.PENDING_APPROVAL.value,
    IncidentStatus.APPROVED.value,
    IncidentStatus.ACTIVE.value,
}
RESOLVED_STATUSES = {IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value}

MOCK_BRIDGES = [
    {
        "bridge": "STS1",
        "incident_id": "OCC-2026001",
        "title": "Payment Gateway timeout spikes",
        "participants": 8,
        "status": "Live",
        "mock": True,
    },
    {
        "bridge": "STS3",
        "incident_id": "OCC-2026003",
        "title": "Wire transfer batch job stalled",
        "participants": 5,
        "status": "Live",
        "mock": True,
    },
    {
        "bridge": "STS2",
        "incident_id": "OCC-2026007",
        "title": "Fraud detection false positives",
        "participants": 11,
        "status": "Live",
        "mock": True,
    },
]

MOCK_ACTIVITIES = [
    {
        "time": "2 min ago",
        "actor": "A. Chen",
        "detail": "Acknowledged Payment Gateway incident on STS1",
        "mock": True,
    },
    {
        "time": "18 min ago",
        "actor": "System",
        "detail": "MOCK: PagerDuty page sent for Fraud Ops after OCC approval",
        "mock": True,
    },
    {
        "time": "41 min ago",
        "actor": "M. Okonkwo",
        "detail": "Submitted SSO login incident for AI analysis",
        "mock": True,
    },
    {
        "time": "1 hr ago",
        "actor": "S. Patel",
        "detail": "Joined STS3 bridge for wire batch backlog",
        "mock": True,
    },
]

MOCK_PENDING_ACKS = [
    {
        "team": "Payments SRE",
        "incident_id": "OCC-2026001",
        "wait_minutes": 4,
        "mock": True,
    },
    {
        "team": "Fraud Ops",
        "incident_id": "OCC-2026007",
        "wait_minutes": 11,
        "mock": True,
    },
    {
        "team": "Identity Platform",
        "incident_id": "OCC-2026002",
        "wait_minutes": 22,
        "mock": True,
    },
]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    settings = get_settings()
    total = db.query(Incident).count()
    active = (
        db.query(Incident)
        .filter(Incident.status.in_(list(ACTIVE_STATUSES)))
        .count()
    )
    critical = (
        db.query(Incident)
        .filter(
            Incident.priority == IncidentPriority.CRITICAL.value,
            Incident.status.in_(list(ACTIVE_STATUSES)),
        )
        .count()
    )
    pending = (
        db.query(Incident)
        .filter(Incident.status == IncidentStatus.PENDING_APPROVAL.value)
        .count()
    )
    bridges = db.query(Incident).filter(Incident.bridge_active.is_(True)).count()
    resolved = (
        db.query(Incident)
        .filter(Incident.status.in_(list(RESOLVED_STATUSES)))
        .count()
    )

    avg_ack = db.query(func.avg(Incident.ack_minutes)).scalar()
    avg_res = db.query(func.avg(Incident.resolution_minutes)).scalar()

    label = "MOCK DATA" if settings.mock_mode else "LIVE DATA"
    return DashboardSummary(
        total_incidents=total,
        active_incidents=active,
        critical_incidents=critical,
        pending_approvals=pending,
        active_bridges=bridges,
        resolved_incidents=resolved,
        avg_ack_minutes=round(float(avg_ack), 1) if avg_ack is not None else None,
        avg_resolution_minutes=round(float(avg_res), 1) if avg_res is not None else None,
        mock_mode=settings.mock_mode,
        data_label=label,
    )


@router.get("", response_model=DashboardBundle)
def dashboard_bundle(db: Session = Depends(get_db)) -> DashboardBundle:
    settings = get_settings()
    summary = dashboard_summary(db)
    active_rows = (
        db.query(Incident)
        .filter(Incident.status.in_(list(ACTIVE_STATUSES)))
        .order_by(Incident.created_at.desc())
        .limit(10)
        .all()
    )
    recent_rows = (
        db.query(Incident).order_by(Incident.created_at.desc()).limit(8).all()
    )

    priority_distribution: dict[str, int] = {
        p.value: 0 for p in IncidentPriority
    }
    for row in db.query(Incident.priority, func.count(Incident.id)).group_by(Incident.priority):
        priority_distribution[row[0]] = row[1]

    pd_rows = (
        db.query(PagerDutyNotification)
        .order_by(PagerDutyNotification.notified_at.desc())
        .limit(12)
        .all()
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    pending_acks = []
    for row in pd_rows:
        if row.acknowledged_at or row.escalation_status != "notified":
            continue
        wait = 1
        if row.notified_at:
            wait = max(1, int((now - row.notified_at).total_seconds() / 60))
        pending_acks.append(
            {
                "team": row.team_name,
                "incident_id": row.occ_incident_id,
                "wait_minutes": wait,
                "status": row.escalation_status,
                "pd_incident_id": row.pd_incident_id,
                "mock": row.is_mock,
            }
        )
    # Seed mock pending acks only when no real PD notifications exist yet
    if not pending_acks and not pd_rows:
        pending_acks = MOCK_PENDING_ACKS

    bridge_rows = (
        db.query(TeamsBridge)
        .order_by(TeamsBridge.created_at.desc())
        .limit(20)
        .all()
    )
    live_active = [
        {
            "bridge": b.bridge_code,
            "incident_id": b.occ_incident_id,
            "title": b.title,
            # Invited count only — not live attendance (Phase 6)
            "participants": invited_count(b),
            "status": b.status.capitalize() if b.status != "open" else "Live",
            "mock": b.is_mock,
            "meeting_url": b.meeting_url,
            "bridge_id": b.id,
        }
        for b in bridge_rows
        if b.status in {"created", "open"}
    ]
    active_bridges = live_active if (live_active or bridge_rows) else MOCK_BRIDGES

    # Keep summary.active_bridges aligned with real open/created bridges when present
    if bridge_rows:
        summary.active_bridges = len(live_active)

    label = "MOCK DATA" if settings.mock_mode else "LIVE DATA"
    return DashboardBundle(
        summary=summary,
        active_incidents=[IncidentRead.model_validate(r) for r in active_rows],
        recent_incidents=[IncidentRead.model_validate(r) for r in recent_rows],
        priority_distribution=priority_distribution,
        recent_activities=MOCK_ACTIVITIES,
        active_bridges=active_bridges,
        pending_acknowledgements=pending_acks,
        pagerduty_notifications=[
            PagerDutyNotificationRead.model_validate(r) for r in pd_rows
        ],
        teams_bridges=_serialize_bridges(bridge_rows[:8]),
        mock_mode=settings.mock_mode,
        data_label=label,
    )


def _serialize_bridges(rows: list[TeamsBridge]) -> list[TeamsBridgeRead]:
    out: list[TeamsBridgeRead] = []
    for row in rows:
        invited: list[dict] = []
        if row.invited_responders:
            try:
                parsed = json.loads(row.invited_responders)
                if isinstance(parsed, list):
                    invited = [x for x in parsed if isinstance(x, dict)]
            except json.JSONDecodeError:
                invited = []
        out.append(
            TeamsBridgeRead(
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
        )
    return out
