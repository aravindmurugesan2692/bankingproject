"""ServiceNow incident creation — MOCK by default; live REST when configured."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.models import Incident


@dataclass
class ServiceNowResult:
    number: str
    sys_id: str
    is_mock: bool
    duplicate: bool
    preview: dict[str, Any]
    raw: dict[str, Any] | None = None


PRIORITY_IMPACT_URGENCY = {
    "P1": ("1", "1"),  # high/high
    "P2": ("2", "2"),
    "P3": ("2", "3"),
    "P4": ("3", "3"),
}


def build_preview(
    incident: Incident,
    *,
    severity: str,
    description: str,
    team_names: list[str],
    analysis_summary: str | None,
) -> dict[str, Any]:
    impact, urgency = PRIORITY_IMPACT_URGENCY.get(severity, ("2", "3"))
    short_description = f"[{incident.occ_incident_id}] {incident.title}"[:160]
    work_notes = (
        f"OCC AI Assistant correlation ID: {incident.occ_incident_id}\n"
        f"Approved severity: {severity}\n"
        f"Approved teams: {', '.join(team_names) or 'none'}\n"
        f"AI summary (hypothesis only): {analysis_summary or 'n/a'}"
    )
    return {
        "short_description": short_description,
        "description": description,
        "category": "inquiry",
        "subcategory": incident.application_service,
        "u_application": incident.application_service,
        "u_environment": incident.environment,
        "business_impact": incident.business_impact,
        "impact": impact,
        "urgency": urgency,
        "priority_code": severity,
        "assignment_group_hint": team_names[0] if team_names else None,
        "approved_teams": team_names,
        "work_notes": work_notes,
        "correlation_id": incident.occ_incident_id,
        "mock_mode": get_settings().mock_mode or not get_settings().servicenow_configured,
    }


def _mock_ids(incident: Incident) -> tuple[str, str]:
    digest = hashlib.sha1(incident.occ_incident_id.encode()).hexdigest()[:8].upper()
    number = f"INC{digest[:7]}"
    sys_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"occ-sn-{incident.occ_incident_id}"))
    return number, sys_id


async def create_incident(
    incident: Incident,
    *,
    severity: str,
    description: str,
    team_names: list[str],
    analysis_summary: str | None,
    settings: Settings | None = None,
) -> ServiceNowResult:
    """Create a ServiceNow incident after OCC approval.

    Duplicate prevention: if incident already has servicenow_sys_id, return it.
    """
    settings = settings or get_settings()
    preview = build_preview(
        incident,
        severity=severity,
        description=description,
        team_names=team_names,
        analysis_summary=analysis_summary,
    )

    if incident.servicenow_sys_id and incident.servicenow_number:
        return ServiceNowResult(
            number=incident.servicenow_number,
            sys_id=incident.servicenow_sys_id,
            is_mock=bool(incident.servicenow_is_mock),
            duplicate=True,
            preview=preview,
            raw={"status": "already_linked"},
        )

    if not settings.use_live_servicenow:
        number, sys_id = _mock_ids(incident)
        return ServiceNowResult(
            number=number,
            sys_id=sys_id,
            is_mock=True,
            duplicate=False,
            preview=preview,
            raw={"mock": True, "payload": preview},
        )

    return await _live_create(incident, preview, settings)


async def _live_create(
    incident: Incident, preview: dict[str, Any], settings: Settings
) -> ServiceNowResult:
    base = settings.servicenow_instance_url.rstrip("/")
    url = f"{base}/api/now/table/incident"
    payload = {
        "short_description": preview["short_description"],
        "description": preview["description"],
        "impact": preview["impact"],
        "urgency": preview["urgency"],
        "work_notes": preview["work_notes"],
        "correlation_id": preview["correlation_id"],
    }
    auth = (settings.servicenow_username, settings.servicenow_password)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=settings.servicenow_timeout_seconds) as client:
        for attempt in range(settings.servicenow_max_retries + 1):
            try:
                # Duplicate check by correlation_id before create
                lookup = await client.get(
                    url,
                    params={
                        "sysparm_query": f"correlation_id={incident.occ_incident_id}",
                        "sysparm_limit": "1",
                    },
                    auth=auth,
                    headers=headers,
                )
                lookup.raise_for_status()
                existing = lookup.json().get("result") or []
                if existing:
                    row = existing[0]
                    return ServiceNowResult(
                        number=row.get("number", ""),
                        sys_id=row.get("sys_id", ""),
                        is_mock=False,
                        duplicate=True,
                        preview=preview,
                        raw=row,
                    )

                response = await client.post(
                    url, json=payload, auth=auth, headers=headers
                )
                response.raise_for_status()
                row = response.json().get("result") or {}
                return ServiceNowResult(
                    number=row.get("number", ""),
                    sys_id=row.get("sys_id", ""),
                    is_mock=False,
                    duplicate=False,
                    preview=preview,
                    raw=row,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= settings.servicenow_max_retries:
                    break

    raise RuntimeError(f"ServiceNow create failed after retries: {last_error}")


def preview_json(preview: dict[str, Any]) -> str:
    return json.dumps(preview, indent=2)
