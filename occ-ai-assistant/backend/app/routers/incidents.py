"""Incident CRUD — Phase 2 auto-runs AI analysis after create."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, IncidentPriority, IncidentStatus
from app.routers.analysis import serialize_analysis
from app.schemas import IncidentCreate, IncidentCreateResponse, IncidentRead
from app.services.ai_analysis import analyze_incident

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _next_occ_id(db: Session) -> str:
    latest = (
        db.query(Incident)
        .order_by(Incident.id.desc())
        .first()
    )
    if latest and latest.occ_incident_id.startswith("OCC-"):
        try:
            num = int(latest.occ_incident_id.split("-", 1)[1])
            return f"OCC-{num + 1}"
        except ValueError:
            pass
    return f"OCC-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"


@router.post("", response_model=IncidentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate, db: Session = Depends(get_db)
) -> IncidentCreateResponse:
    incident = Incident(
        occ_incident_id=_next_occ_id(db),
        title=payload.title,
        description=payload.description,
        application_service=payload.application_service,
        environment=payload.environment,
        business_impact=payload.business_impact,
        users_affected=payload.users_affected,
        issue_start_time=payload.issue_start_time,
        error_messages=payload.error_messages,
        affected_infrastructure=payload.affected_infrastructure,
        additional_observations=payload.additional_observations,
        status=IncidentStatus.NEW.value,
        priority=IncidentPriority.MEDIUM.value,
        is_mock=False,
        created_by=payload.created_by or "OCC Engineer",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    analysis = await analyze_incident(db, incident)
    return IncidentCreateResponse(
        incident=IncidentRead.model_validate(incident),
        analysis=serialize_analysis(analysis, incident),
    )


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db)) -> list[Incident]:
    return db.query(Incident).order_by(Incident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
