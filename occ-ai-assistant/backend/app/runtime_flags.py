"""Runtime force-mock overrides — secrets never stored here."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import RuntimeSetting

FORCE_KEYS = {
    "force_mock_llm",
    "force_mock_servicenow",
    "force_mock_pagerduty",
    "force_mock_teams",
}


def get_flag(db: Session, key: str, default: str = "false") -> str:
    row = db.query(RuntimeSetting).filter(RuntimeSetting.key == key).first()
    return (row.value if row else default) or default


def get_bool(db: Session, key: str, default: bool = False) -> bool:
    return get_flag(db, key, "true" if default else "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def set_flag(db: Session, key: str, value: str, *, actor: str) -> RuntimeSetting:
    row = db.query(RuntimeSetting).filter(RuntimeSetting.key == key).first()
    if not row:
        row = RuntimeSetting(key=key, value=value, updated_by=actor)
        db.add(row)
    else:
        row.value = value
        row.updated_by = actor
    db.commit()
    db.refresh(row)
    return row


def all_force_mocks(db: Session) -> dict[str, bool]:
    return {k: get_bool(db, k, False) for k in FORCE_KEYS}
