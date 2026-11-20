"""Auth-ready RBAC — demo header identity today; OIDC/JWT hook later.

Roles:
  - occ_engineer — day-to-day OCC operations including approvals
  - occ_administrator — engineer permissions + settings / force-mock toggles

Never trust frontend for secrets. Credentials stay in env only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ApprovalAction, SecurityAuditEvent, utc_now


class Role(str, Enum):
    OCC_ENGINEER = "occ_engineer"
    OCC_ADMINISTRATOR = "occ_administrator"
    # Read-only demo role — used to exercise 403 denial paths (not a production persona)
    VIEWER = "viewer"


class Permission(str, Enum):
    INCIDENT_READ = "incident:read"
    INCIDENT_WRITE = "incident:write"
    INCIDENT_APPROVE = "incident:approve"
    INCIDENT_REJECT = "incident:reject"
    NOTIFICATION_TRIGGER = "notification:trigger"
    CLOSURE_DRAFT = "closure:draft"
    CLOSURE_SUBMIT = "closure:submit"
    CLOSURE_APPROVE = "closure:approve"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OCC_ENGINEER: {
        Permission.INCIDENT_READ,
        Permission.INCIDENT_WRITE,
        Permission.INCIDENT_APPROVE,
        Permission.INCIDENT_REJECT,
        Permission.NOTIFICATION_TRIGGER,
        Permission.CLOSURE_DRAFT,
        Permission.CLOSURE_SUBMIT,
        Permission.CLOSURE_APPROVE,
        Permission.SETTINGS_READ,
        Permission.AUDIT_READ,
    },
    Role.OCC_ADMINISTRATOR: {
        Permission.INCIDENT_READ,
        Permission.INCIDENT_WRITE,
        Permission.INCIDENT_APPROVE,
        Permission.INCIDENT_REJECT,
        Permission.NOTIFICATION_TRIGGER,
        Permission.CLOSURE_DRAFT,
        Permission.CLOSURE_SUBMIT,
        Permission.CLOSURE_APPROVE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_WRITE,
        Permission.AUDIT_READ,
    },
    Role.VIEWER: {
        Permission.INCIDENT_READ,
        Permission.SETTINGS_READ,
    },
}


@dataclass(frozen=True)
class Principal:
    user_id: str
    display_name: str
    role: Role

    def has(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


def _parse_role(raw: str | None) -> Role:
    value = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "engineer": Role.OCC_ENGINEER,
        "occ_engineer": Role.OCC_ENGINEER,
        "admin": Role.OCC_ADMINISTRATOR,
        "administrator": Role.OCC_ADMINISTRATOR,
        "occ_administrator": Role.OCC_ADMINISTRATOR,
        "occ_admin": Role.OCC_ADMINISTRATOR,
        "viewer": Role.VIEWER,
        "read_only": Role.VIEWER,
    }
    return aliases.get(value, Role.OCC_ENGINEER)


def resolve_principal(
    *,
    x_occ_user: str | None = None,
    x_occ_role: str | None = None,
) -> Principal:
    """Resolve caller identity.

    AUTH_DEMO_ENABLED (default true): accept X-OCC-User / X-OCC-Role headers.
    AUTH_MODE=disabled: anonymous engineer for local tests.
    Future: AUTH_MODE=oidc validates bearer tokens (not implemented — no invented credentials).
    """
    settings = get_settings()
    mode = (settings.auth_mode or "demo").strip().lower()

    if mode == "oidc":
        # Auth-ready stub — refuse until real IdP is wired (never invent tokens).
        raise HTTPException(
            status_code=501,
            detail="OIDC auth mode is not configured. Set AUTH_MODE=demo for local use.",
        )

    if mode == "disabled" or not settings.auth_demo_enabled:
        return Principal(
            user_id="demo-local",
            display_name=settings.auth_default_user,
            role=_parse_role(settings.auth_default_role),
        )

    name = (x_occ_user or settings.auth_default_user).strip() or "OCC Engineer · Demo User"
    role = _parse_role(x_occ_role or settings.auth_default_role)
    return Principal(
        user_id=name.lower().replace(" ", "-")[:64],
        display_name=name[:128],
        role=role,
    )


async def get_current_principal(
    x_occ_user: Annotated[str | None, Header()] = None,
    x_occ_role: Annotated[str | None, Header()] = None,
) -> Principal:
    return resolve_principal(x_occ_user=x_occ_user, x_occ_role=x_occ_role)


def _log_denial(
    db: Session,
    principal: Principal,
    permission: Permission,
    request: Request | None,
) -> None:
    path = request.url.path if request else ""
    db.add(
        SecurityAuditEvent(
            action=ApprovalAction.SECURITY_DENIED.value,
            actor=principal.display_name,
            role=principal.role.value,
            detail=f"Denied {permission.value}",
            path=path[:255] if path else None,
        )
    )
    db.commit()


def require_permission(permission: Permission) -> Callable:
    """FastAPI dependency factory — enforces RBAC and audits denials."""

    async def _dep(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_principal)],
        db: Session = Depends(get_db),
    ) -> Principal:
        if principal.has(permission):
            return principal
        try:
            _log_denial(db, principal, permission, request)
        except Exception:  # noqa: BLE001 — never block denial response on audit failure
            pass
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {permission.value} requires an authorized OCC role",
        )

    return _dep


# Convenience aliases for routers
RequireApprove = Annotated[Principal, Depends(require_permission(Permission.INCIDENT_APPROVE))]
RequireReject = Annotated[Principal, Depends(require_permission(Permission.INCIDENT_REJECT))]
RequireClosureApprove = Annotated[
    Principal, Depends(require_permission(Permission.CLOSURE_APPROVE))
]
RequireSettingsWrite = Annotated[
    Principal, Depends(require_permission(Permission.SETTINGS_WRITE))
]
RequireSettingsRead = Annotated[
    Principal, Depends(require_permission(Permission.SETTINGS_READ))
]
RequireIncidentWrite = Annotated[
    Principal, Depends(require_permission(Permission.INCIDENT_WRITE))
]


def role_catalog() -> list[dict]:
    return [
        {
            "role": Role.OCC_ENGINEER.value,
            "label": "OCC Engineer",
            "permissions": sorted(p.value for p in ROLE_PERMISSIONS[Role.OCC_ENGINEER]),
        },
        {
            "role": Role.OCC_ADMINISTRATOR.value,
            "label": "OCC Administrator",
            "permissions": sorted(p.value for p in ROLE_PERMISSIONS[Role.OCC_ADMINISTRATOR]),
        },
        {
            "role": Role.VIEWER.value,
            "label": "Viewer (read-only demo)",
            "permissions": sorted(p.value for p in ROLE_PERMISSIONS[Role.VIEWER]),
        },
    ]


# silence unused import warning for utc_now if lint complains — kept for future token expiry
_ = utc_now
