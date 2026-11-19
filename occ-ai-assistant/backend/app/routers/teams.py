"""Support team catalog APIs."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SupportTeam
from app.schemas import SupportTeamRead

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[SupportTeamRead])
def list_teams(db: Session = Depends(get_db)) -> list[SupportTeam]:
    return (
        db.query(SupportTeam)
        .order_by(SupportTeam.name.asc())
        .all()
    )
