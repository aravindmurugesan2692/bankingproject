"""Settings — public status only; secrets never returned to frontend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import (
    RequireSettingsRead,
    RequireSettingsWrite,
    Role,
    get_current_principal,
    role_catalog,
)
from app.config import get_settings
from app.database import get_db
from app.models import ApprovalAction, SecurityAuditEvent
from app.runtime_flags import FORCE_KEYS, all_force_mocks, set_flag

router = APIRouter(prefix="/settings", tags=["settings"])


class IntegrationStatus(BaseModel):
    name: str
    configured: bool
    live_eligible: bool  # would be live if MOCK_MODE=false and configured
    force_mock: bool
    effectively_mock: bool
    note: str


class SettingsStatus(BaseModel):
    mock_mode: bool
    auth_mode: str
    auth_demo_enabled: bool
    current_user: str
    current_role: str
    permissions: list[str]
    roles: list[dict]
    integrations: list[IntegrationStatus]
    force_mocks: dict[str, bool]
    data_label: str
    secrets_in_frontend: bool = False
    note: str


class ForceMockUpdate(BaseModel):
    force_mock_llm: bool | None = None
    force_mock_servicenow: bool | None = None
    force_mock_pagerduty: bool | None = None
    force_mock_teams: bool | None = None
    actor: str = Field(default="OCC Administrator · Demo User", max_length=128)


class DemoIdentityUpdate(BaseModel):
    """Client-side demo identity hint — actual enforcement uses request headers."""

    display_name: str = Field(default="OCC Engineer · Demo User", max_length=128)
    role: str = Field(default="occ_engineer", max_length=64)


def _integration_rows(db: Session) -> list[IntegrationStatus]:
    settings = get_settings()
    forces = all_force_mocks(db)

    def row(
        name: str,
        configured: bool,
        live_prop: bool,
        force_key: str,
        note: str,
    ) -> IntegrationStatus:
        force = forces.get(force_key, False)
        return IntegrationStatus(
            name=name,
            configured=configured,
            live_eligible=live_prop and not settings.mock_mode,
            force_mock=force,
            effectively_mock=settings.mock_mode or not configured or force or not live_prop,
            note=note,
        )

    return [
        row(
            "LLM",
            bool(settings.openai_api_key.strip()),
            settings.use_live_llm,
            "force_mock_llm",
            "OPENAI_API_KEY via env only",
        ),
        row(
            "ServiceNow",
            settings.servicenow_configured,
            settings.use_live_servicenow,
            "force_mock_servicenow",
            "Instance URL + username/password or OAuth client via env",
        ),
        row(
            "PagerDuty",
            settings.pagerduty_configured,
            settings.use_live_pagerduty,
            "force_mock_pagerduty",
            "PAGERDUTY_API_KEY via env only",
        ),
        row(
            "Microsoft Teams / Graph",
            settings.microsoft_graph_configured,
            settings.use_live_teams,
            "force_mock_teams",
            "Tenant + client id/secret via env only",
        ),
    ]


@router.get("", response_model=SettingsStatus)
def get_settings_status(
    principal: RequireSettingsRead,
    db: Session = Depends(get_db),
) -> SettingsStatus:
    settings = get_settings()
    from app.auth import ROLE_PERMISSIONS

    return SettingsStatus(
        mock_mode=settings.mock_mode,
        auth_mode=settings.auth_mode,
        auth_demo_enabled=settings.auth_demo_enabled,
        current_user=principal.display_name,
        current_role=principal.role.value,
        permissions=sorted(p.value for p in ROLE_PERMISSIONS[principal.role]),
        roles=role_catalog(),
        integrations=_integration_rows(db),
        force_mocks=all_force_mocks(db),
        data_label="MOCK MODE" if settings.mock_mode else "LIVE MODE (env)",
        secrets_in_frontend=False,
        note=(
            "MOCK_MODE and API credentials are environment-only. "
            "Administrators may force mock per integration without storing secrets. "
            "Restart the process to change MOCK_MODE itself."
        ),
    )


@router.get("/me")
def whoami(principal=Depends(get_current_principal)):
    from app.auth import ROLE_PERMISSIONS

    return {
        "user_id": principal.user_id,
        "display_name": principal.display_name,
        "role": principal.role.value,
        "permissions": sorted(p.value for p in ROLE_PERMISSIONS[principal.role]),
    }


@router.patch("/force-mocks", response_model=SettingsStatus)
def update_force_mocks(
    payload: ForceMockUpdate,
    principal: RequireSettingsWrite,
    db: Session = Depends(get_db),
) -> SettingsStatus:
    mapping = {
        "force_mock_llm": payload.force_mock_llm,
        "force_mock_servicenow": payload.force_mock_servicenow,
        "force_mock_pagerduty": payload.force_mock_pagerduty,
        "force_mock_teams": payload.force_mock_teams,
    }
    changed = []
    for key, value in mapping.items():
        if value is None:
            continue
        if key not in FORCE_KEYS:
            continue
        set_flag(db, key, "true" if value else "false", actor=principal.display_name)
        changed.append(f"{key}={'true' if value else 'false'}")

    db.add(
        SecurityAuditEvent(
            action=ApprovalAction.SETTINGS_UPDATE.value,
            actor=principal.display_name,
            role=principal.role.value,
            detail=f"Updated force-mock flags: {', '.join(changed) or 'none'}",
            path="/api/settings/force-mocks",
        )
    )
    db.commit()
    return get_settings_status(principal, db)


@router.post("/demo-identity")
def record_demo_identity(
    payload: DemoIdentityUpdate,
    principal: RequireSettingsRead,
    db: Session = Depends(get_db),
):
    """Audit demo role switch — client must send matching X-OCC-* headers afterward."""
    role = payload.role.strip().lower()
    if role not in {
        Role.OCC_ENGINEER.value,
        Role.OCC_ADMINISTRATOR.value,
        Role.VIEWER.value,
    }:
        role = Role.OCC_ENGINEER.value
    db.add(
        SecurityAuditEvent(
            action=ApprovalAction.AUTH_DEMO_SWITCH.value,
            actor=principal.display_name,
            role=role,
            detail=(
                f"Demo identity intent → user={payload.display_name[:64]} role={role} "
                f"(client must set X-OCC-User / X-OCC-Role)"
            ),
            path="/api/settings/demo-identity",
        )
    )
    db.commit()
    return {
        "ok": True,
        "display_name": payload.display_name,
        "role": role,
        "headers": {"X-OCC-User": payload.display_name, "X-OCC-Role": role},
        "note": "Store headers in the client session; secrets are never returned.",
    }
