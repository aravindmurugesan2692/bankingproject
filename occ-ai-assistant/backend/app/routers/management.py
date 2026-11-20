"""Incident Management — history, reporting, closure (Phase 8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, IncidentClosure
from app.schemas import (
    ClosureActorRequest,
    ClosureDraftUpdate,
    ClosureRejectRequest,
    IncidentClosureRead,
    IncidentRead,
    ManagementDetail,
    ManagementHistoryItem,
    ManagementHistoryResponse,
    ReportingMetrics,
)
from app.services import closure as closure_svc
from app.services import management as mgmt

router = APIRouter(prefix="/management", tags=["management"])


@router.get("/history", response_model=ManagementHistoryResponse)
def list_history(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    application: str | None = Query(default=None),
    is_mock: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ManagementHistoryResponse:
    from app.config import get_settings

    total, rows = mgmt.search_history(
        db,
        q=q,
        status=status,
        environment=environment,
        severity=severity,
        application=application,
        is_mock=is_mock,
        limit=limit,
        offset=offset,
    )
    items = [ManagementHistoryItem(**mgmt.history_item(db, row)) for row in rows]
    settings = get_settings()
    mock_n = sum(1 for i in items if i.is_mock)
    label = (
        "MIXED — includes MOCK seeded rows"
        if mock_n and mock_n < len(items)
        else ("MOCK DATA" if mock_n or settings.mock_mode else "LIVE DATA")
    )
    return ManagementHistoryResponse(
        total=total,
        items=items,
        data_label=label,
        mock_mode=settings.mock_mode,
    )


@router.get("/incidents/{incident_id}", response_model=ManagementDetail)
def get_detail(incident_id: int, db: Session = Depends(get_db)) -> ManagementDetail:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    bundle = mgmt.detail_bundle(db, incident)
    return ManagementDetail(
        incident=IncidentRead.model_validate(bundle["incident"]),
        pagerduty_incident_ids=bundle["pagerduty_incident_ids"],
        assigned_teams=bundle["assigned_teams"],
        bridge_duration_minutes=bundle["bridge_duration_minutes"],
        closure=(
            IncidentClosureRead.model_validate(bundle["closure"])
            if bundle["closure"]
            else None
        ),
        timeline_event_count=bundle["timeline_event_count"],
        analysis_category=bundle["analysis_category"],
        is_mock=bundle["is_mock"],
        data_label=bundle["data_label"],
    )


@router.get("/metrics", response_model=ReportingMetrics)
def get_metrics(db: Session = Depends(get_db)) -> ReportingMetrics:
    return ReportingMetrics(**mgmt.reporting_metrics(db))


@router.get(
    "/incidents/{incident_id}/closure",
    response_model=IncidentClosureRead,
)
def get_or_open_closure(
    incident_id: int,
    actor: str = Query(default="OCC Engineer · Demo User"),
    db: Session = Depends(get_db),
) -> IncidentClosure:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    # Return latest completed if already closed
    latest = (
        db.query(IncidentClosure)
        .filter(IncidentClosure.incident_id == incident_id)
        .order_by(IncidentClosure.id.desc())
        .first()
    )
    if latest and latest.status == "completed":
        return latest
    if latest and latest.status in {"draft", "pending_occ", "rejected", "approved"}:
        return latest
    return closure_svc.get_or_create_draft(db, incident, actor=actor)


@router.post(
    "/incidents/{incident_id}/closure",
    response_model=IncidentClosureRead,
)
def open_closure(
    incident_id: int,
    payload: ClosureActorRequest,
    db: Session = Depends(get_db),
) -> IncidentClosure:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return closure_svc.get_or_create_draft(db, incident, actor=payload.actor)


@router.patch("/closures/{closure_id}", response_model=IncidentClosureRead)
def patch_closure(
    closure_id: int,
    payload: ClosureDraftUpdate,
    db: Session = Depends(get_db),
) -> IncidentClosure:
    row = db.query(IncidentClosure).filter(IncidentClosure.id == closure_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Closure not found")
    return closure_svc.update_draft(
        db,
        row,
        restored_at=payload.restored_at,
        final_summary=payload.final_summary,
        timeline_summary=payload.timeline_summary,
        team_notes=payload.team_notes,
        remediation_notes=payload.remediation_notes,
        rca_status=payload.rca_status,
        rca_statement=payload.rca_statement,
        refresh_timeline=payload.refresh_timeline,
        actor=payload.actor,
    )


@router.post("/closures/{closure_id}/submit", response_model=IncidentClosureRead)
def submit_closure(
    closure_id: int,
    payload: ClosureActorRequest,
    db: Session = Depends(get_db),
) -> IncidentClosure:
    row = db.query(IncidentClosure).filter(IncidentClosure.id == closure_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Closure not found")
    return closure_svc.submit_for_occ(db, row, actor=payload.actor)


@router.post("/closures/{closure_id}/approve", response_model=IncidentClosureRead)
async def approve_closure(
    closure_id: int,
    payload: ClosureActorRequest,
    db: Session = Depends(get_db),
) -> IncidentClosure:
    row = db.query(IncidentClosure).filter(IncidentClosure.id == closure_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Closure not found")
    return await closure_svc.approve_and_complete(
        db, row, actor=payload.actor, close_fully=payload.close_fully
    )


@router.post("/closures/{closure_id}/reject", response_model=IncidentClosureRead)
def reject_closure(
    closure_id: int,
    payload: ClosureRejectRequest,
    db: Session = Depends(get_db),
) -> IncidentClosure:
    row = db.query(IncidentClosure).filter(IncidentClosure.id == closure_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Closure not found")
    return closure_svc.reject_closure(
        db, row, actor=payload.actor, reason=payload.reason
    )
