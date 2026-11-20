"""Incident history search + reporting metrics (Phase 8)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    BridgeAttendance,
    Incident,
    IncidentAnalysis,
    IncidentClosure,
    IncidentStatus,
    PagerDutyNotification,
    TeamsBridge,
)


def _slugs(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (TypeError, json.JSONDecodeError):
        pass
    return []


def _bridge_minutes(db: Session, incident_id: int) -> int | None:
    bridges = (
        db.query(TeamsBridge).filter(TeamsBridge.incident_id == incident_id).all()
    )
    total = 0
    any_ended = False
    for b in bridges:
        if b.started_at and b.ended_at:
            any_ended = True
            total += max(0, int((b.ended_at - b.started_at).total_seconds() / 60))
        elif b.started_at and not b.ended_at:
            any_ended = True
            end = datetime.utcnow()
            total += max(0, int((end - b.started_at).total_seconds() / 60))
    return total if any_ended else None


def _pd_ids(db: Session, incident_id: int) -> list[str]:
    rows = (
        db.query(PagerDutyNotification)
        .filter(PagerDutyNotification.incident_id == incident_id)
        .all()
    )
    return [r.pd_incident_id for r in rows if r.pd_incident_id]


def _latest_closure(db: Session, incident_id: int) -> IncidentClosure | None:
    return (
        db.query(IncidentClosure)
        .filter(IncidentClosure.incident_id == incident_id)
        .order_by(IncidentClosure.id.desc())
        .first()
    )


def history_item(db: Session, incident: Incident) -> dict[str, Any]:
    closure = _latest_closure(db, incident.id)
    return {
        "id": incident.id,
        "occ_incident_id": incident.occ_incident_id,
        "servicenow_number": incident.servicenow_number,
        "pagerduty_incident_ids": _pd_ids(db, incident.id),
        "title": incident.title,
        "application_service": incident.application_service,
        "environment": incident.environment,
        "priority": incident.priority,
        "working_severity": incident.working_severity,
        "status": incident.status,
        "assigned_teams": _slugs(incident.selected_team_slugs),
        "created_at": incident.created_at,
        "issue_start_time": incident.issue_start_time,
        "ack_minutes": incident.ack_minutes,
        "resolution_minutes": incident.resolution_minutes,
        "bridge_duration_minutes": _bridge_minutes(db, incident.id),
        "restored_at": incident.restored_at,
        "closed_at": incident.closed_at,
        "rca_status": incident.rca_status,
        "is_mock": incident.is_mock,
        "closure_status": closure.status if closure else None,
    }


def search_history(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    environment: str | None = None,
    severity: str | None = None,
    application: str | None = None,
    is_mock: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Incident]]:
    query = db.query(Incident)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Incident.occ_incident_id.ilike(like),
                Incident.title.ilike(like),
                Incident.servicenow_number.ilike(like),
                Incident.application_service.ilike(like),
            )
        )
    if status:
        query = query.filter(Incident.status == status)
    if environment:
        query = query.filter(Incident.environment == environment)
    if severity:
        query = query.filter(
            or_(
                Incident.working_severity == severity,
                Incident.priority == severity,
            )
        )
    if application:
        query = query.filter(Incident.application_service.ilike(f"%{application}%"))
    if is_mock is not None:
        query = query.filter(Incident.is_mock == is_mock)

    total = query.count()
    rows = (
        query.order_by(Incident.created_at.desc())
        .offset(max(0, offset))
        .limit(min(200, max(1, limit)))
        .all()
    )
    return total, rows


def detail_bundle(db: Session, incident: Incident) -> dict[str, Any]:
    settings = get_settings()
    analysis = (
        db.query(IncidentAnalysis)
        .filter(IncidentAnalysis.incident_id == incident.id)
        .order_by(IncidentAnalysis.id.desc())
        .first()
    )
    closure = _latest_closure(db, incident.id)
    from app.models import TimelineEvent

    tl_count = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.incident_id == incident.id)
        .count()
    )
    label = "MOCK DATA" if incident.is_mock or settings.mock_mode else "LIVE DATA"
    return {
        "incident": incident,
        "pagerduty_incident_ids": _pd_ids(db, incident.id),
        "assigned_teams": _slugs(incident.selected_team_slugs),
        "bridge_duration_minutes": _bridge_minutes(db, incident.id),
        "closure": closure,
        "timeline_event_count": tl_count,
        "analysis_category": analysis.category if analysis else None,
        "is_mock": incident.is_mock,
        "data_label": label,
    }


def reporting_metrics(db: Session) -> dict[str, Any]:
    settings = get_settings()
    incidents = db.query(Incident).all()
    analyses = db.query(IncidentAnalysis).all()
    by_inc_analysis = {a.incident_id: a for a in analyses}

    cat_counter: Counter[str] = Counter()
    for a in analyses:
        cat_counter[a.category or "Uncategorized"] += 1

    team_counter: Counter[str] = Counter()
    for inc in incidents:
        for slug in _slugs(inc.selected_team_slugs):
            team_counter[slug] += 1

    app_counter: Counter[str] = Counter()
    sev_counter: Counter[str] = Counter()
    for inc in incidents:
        app_counter[inc.application_service] += 1
        sev = inc.working_severity or inc.priority or "Unknown"
        sev_counter[sev] += 1

    # Repeat = same application + similar title prefix among 2+
    title_groups: dict[str, list[Incident]] = defaultdict(list)
    for inc in incidents:
        key = f"{inc.application_service}::{inc.title.strip().lower()[:40]}"
        title_groups[key].append(inc)
    repeats = []
    for key, group in title_groups.items():
        if len(group) < 2:
            continue
        repeats.append(
            {
                "key": key,
                "count": len(group),
                "application": group[0].application_service,
                "sample_title": group[0].title,
                "occ_ids": [g.occ_incident_id for g in group],
                "includes_mock": any(g.is_mock for g in group),
            }
        )
    repeats.sort(key=lambda x: -x["count"])

    acks = [i.ack_minutes for i in incidents if i.ack_minutes is not None]
    res = [i.resolution_minutes for i in incidents if i.resolution_minutes is not None]
    avg_ack = round(sum(acks) / len(acks), 1) if acks else None
    avg_res = round(sum(res) / len(res), 1) if res else None

    # Team participation from attendance
    part_counter: Counter[str] = Counter()
    attendance = db.query(BridgeAttendance).all()
    for row in attendance:
        label = row.team_slug or row.display_name or "unknown"
        part_counter[label] += 1

    # SLA-ish trends by month of creation
    month_buckets: dict[str, dict[str, Any]] = {}
    for inc in incidents:
        month = (inc.created_at or datetime.utcnow()).strftime("%Y-%m")
        bucket = month_buckets.setdefault(
            month, {"month": month, "count": 0, "ack_sum": 0, "ack_n": 0, "res_sum": 0, "res_n": 0}
        )
        bucket["count"] += 1
        if inc.ack_minutes is not None:
            bucket["ack_sum"] += inc.ack_minutes
            bucket["ack_n"] += 1
        if inc.resolution_minutes is not None:
            bucket["res_sum"] += inc.resolution_minutes
            bucket["res_n"] += 1
    sla_trends = []
    for month in sorted(month_buckets.keys()):
        b = month_buckets[month]
        sla_trends.append(
            {
                "month": month,
                "incident_count": b["count"],
                "avg_ack_minutes": round(b["ack_sum"] / b["ack_n"], 1) if b["ack_n"] else None,
                "avg_resolution_minutes": (
                    round(b["res_sum"] / b["res_n"], 1) if b["res_n"] else None
                ),
            }
        )

    closures = db.query(IncidentClosure).all()
    pending_closure = sum(1 for c in closures if c.status in {"draft", "pending_occ", "rejected"})
    closed = sum(
        1
        for i in incidents
        if i.status in {IncidentStatus.CLOSED.value, IncidentStatus.RESOLVED.value}
    )
    mock_n = sum(1 for i in incidents if i.is_mock)
    live_n = len(incidents) - mock_n

    # Include unused analysis map to keep lint quiet / future enrichment
    _ = by_inc_analysis

    return {
        "total_incidents": len(incidents),
        "by_category": [
            {"category": k, "count": v} for k, v in cat_counter.most_common(20)
        ],
        "by_support_team": [
            {"team_slug": k, "count": v} for k, v in team_counter.most_common(20)
        ],
        "avg_ack_minutes": avg_ack,
        "avg_resolution_minutes": avg_res,
        "repeat_incidents": repeats[:20],
        "volume_by_application": [
            {"application": k, "count": v} for k, v in app_counter.most_common(20)
        ],
        "volume_by_severity": [
            {"severity": k, "count": v} for k, v in sev_counter.most_common()
        ],
        "team_participation": [
            {"team": k, "attendance_records": v}
            for k, v in part_counter.most_common(20)
        ],
        "sla_trends": sla_trends,
        "closed_count": closed,
        "pending_closure_count": pending_closure,
        "mock_incident_count": mock_n,
        "live_incident_count": live_n,
        "data_label": "MIXED — seeded MOCK + live app rows" if mock_n and live_n else (
            "MOCK DATA" if mock_n or settings.mock_mode else "LIVE DATA"
        ),
        "mock_mode": settings.mock_mode,
    }
