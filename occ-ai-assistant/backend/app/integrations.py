"""Effective live-vs-mock decisions (env MOCK_MODE + admin force-mock flags)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.runtime_flags import get_bool


def live_llm(db: Session | None = None) -> bool:
    settings = get_settings()
    if not settings.use_live_llm:
        return False
    if db is not None and get_bool(db, "force_mock_llm"):
        return False
    return True


def live_servicenow(db: Session | None = None) -> bool:
    settings = get_settings()
    if not settings.use_live_servicenow:
        return False
    if db is not None and get_bool(db, "force_mock_servicenow"):
        return False
    return True


def live_pagerduty(db: Session | None = None) -> bool:
    settings = get_settings()
    if not settings.use_live_pagerduty:
        return False
    if db is not None and get_bool(db, "force_mock_pagerduty"):
        return False
    return True


def live_teams(db: Session | None = None) -> bool:
    settings = get_settings()
    if not settings.use_live_teams:
        return False
    if db is not None and get_bool(db, "force_mock_teams"):
        return False
    return True
