"""Incident analysis APIs."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, IncidentAnalysis
from app.schemas import IncidentAnalysisRead, RecommendedTeam
from app.services.ai_analysis import analyze_incident

router = APIRouter(tags=["analysis"])


def serialize_analysis(analysis: IncidentAnalysis, incident: Incident | None = None) -> IncidentAnalysisRead:
    incident = incident or analysis.incident
    return IncidentAnalysisRead(
        id=analysis.id,
        incident_id=analysis.incident_id,
        occ_incident_id=incident.occ_incident_id if incident else None,
        incident_title=incident.title if incident else None,
        summary=analysis.summary,
        category=analysis.category,
        suggested_priority=analysis.suggested_priority,
        business_impact=analysis.business_impact,
        potential_causes=json.loads(analysis.potential_causes),
        affected_application=analysis.affected_application,
        recommended_teams=[
            RecommendedTeam(**item) for item in json.loads(analysis.recommended_teams)
        ],
        troubleshooting_steps=json.loads(analysis.troubleshooting_steps),
        missing_information=json.loads(analysis.missing_information),
        next_actions=json.loads(analysis.next_actions),
        needs_more_info=analysis.needs_more_info,
        disclaimer=analysis.disclaimer,
        provider=analysis.provider,
        model=analysis.model,
        is_mock=analysis.is_mock,
        created_at=analysis.created_at,
    )


@router.get("/analyses", response_model=list[IncidentAnalysisRead])
def list_analyses(db: Session = Depends(get_db)) -> list[IncidentAnalysisRead]:
    rows = (
        db.query(IncidentAnalysis)
        .order_by(IncidentAnalysis.created_at.desc())
        .limit(50)
        .all()
    )
    return [serialize_analysis(row) for row in rows]


@router.get("/incidents/{incident_id}/analysis", response_model=IncidentAnalysisRead)
def get_latest_analysis(incident_id: int, db: Session = Depends(get_db)) -> IncidentAnalysisRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analysis = (
        db.query(IncidentAnalysis)
        .filter(IncidentAnalysis.incident_id == incident_id)
        .order_by(IncidentAnalysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return serialize_analysis(analysis, incident)


@router.post("/incidents/{incident_id}/analysis", response_model=IncidentAnalysisRead)
async def rerun_analysis(incident_id: int, db: Session = Depends(get_db)) -> IncidentAnalysisRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    analysis = await analyze_incident(db, incident)
    return serialize_analysis(analysis, incident)
