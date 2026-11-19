"""PagerDuty incident notifications — MOCK by default; live Events/API when configured.

Never call this without explicit OCC approval (enforced by callers).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Incident, PagerDutyNotification, SupportTeam, utc_now


@dataclass
class PageResult:
    team_slug: str
    team_name: str
    service_id: str
    escalation_policy_id: str
    pd_incident_id: str
    pd_incident_url: str
    escalation_status: str
    is_mock: bool
    duplicate: bool
    raw: dict[str, Any] | None = None


SEVERITY_MAP = {
    "P1": "critical",
    "P2": "error",
    "P3": "warning",
    "P4": "info",
}


def _mock_ids(incident: Incident, team: SupportTeam) -> tuple[str, str]:
    digest = hashlib.sha1(
        f"{incident.occ_incident_id}:{team.slug}".encode()
    ).hexdigest()[:12]
    pd_id = f"PDMOCK{digest.upper()}"
    url = f"https://mock.pagerduty.local/incidents/{pd_id}"
    return pd_id, url


async def page_team(
    incident: Incident,
    team: SupportTeam,
    *,
    severity: str,
    settings: Settings | None = None,
) -> PageResult:
    settings = settings or get_settings()
    service_id = team.pagerduty_service_id or f"PD_SVC_{team.slug.upper()}_PLACEHOLDER"
    esc_id = (
        team.pagerduty_escalation_policy_id
        or f"PD_ESC_{team.slug.upper()}_PLACEHOLDER"
    )

    if not settings.use_live_pagerduty:
        pd_id, url = _mock_ids(incident, team)
        return PageResult(
            team_slug=team.slug,
            team_name=team.name,
            service_id=service_id,
            escalation_policy_id=esc_id,
            pd_incident_id=pd_id,
            pd_incident_url=url,
            escalation_status="notified",
            is_mock=True,
            duplicate=False,
            raw={
                "mock": True,
                "title": incident.title,
                "severity": SEVERITY_MAP.get(severity, "warning"),
                "dedup_key": f"{incident.occ_incident_id}:{team.slug}",
                "service_id": service_id,
                "escalation_policy_id": esc_id,
                "links": {
                    "occ": incident.occ_incident_id,
                    "servicenow": incident.servicenow_number,
                },
            },
        )

    return await _live_page(incident, team, severity, service_id, esc_id, settings)


async def _live_page(
    incident: Incident,
    team: SupportTeam,
    severity: str,
    service_id: str,
    esc_id: str,
    settings: Settings,
) -> PageResult:
    """Create via PagerDuty Events API v2 (service routing key optional) / Incidents API.

    Uses Incidents API with service id when available.
    """
    base = settings.pagerduty_api_url.rstrip("/")
    headers = {
        "Authorization": f"Token token={settings.pagerduty_key}",
        "Accept": "application/vnd.pagerduty+json;version=2",
        "Content-Type": "application/json",
        "From": "occ-ai-assistant@example.local",
    }
    body = {
        "incident": {
            "type": "incident",
            "title": f"[{incident.occ_incident_id}] {incident.title}",
            "service": {"id": service_id.replace("PD_SVC_", "")[:7] or service_id, "type": "service_reference"},
            "urgency": "high" if severity in {"P1", "P2"} else "low",
            "body": {
                "type": "incident_body",
                "details": (
                    f"OCC: {incident.occ_incident_id}\n"
                    f"ServiceNow: {incident.servicenow_number or 'n/a'}\n"
                    f"Team: {team.name}\n"
                    f"{incident.description[:1500]}"
                ),
            },
        }
    }
    # If service id is still a placeholder, fall back to mock rather than fail hard
    if "PLACEHOLDER" in service_id.upper():
        pd_id, url = _mock_ids(incident, team)
        return PageResult(
            team_slug=team.slug,
            team_name=team.name,
            service_id=service_id,
            escalation_policy_id=esc_id,
            pd_incident_id=pd_id,
            pd_incident_url=url,
            escalation_status="notified",
            is_mock=True,
            duplicate=False,
            raw={"fallback_mock": True, "reason": "placeholder service id"},
        )

    async with httpx.AsyncClient(timeout=settings.pagerduty_timeout_seconds) as client:
        response = await client.post(f"{base}/incidents", headers=headers, json=body)
        response.raise_for_status()
        data = response.json().get("incident") or {}
        pd_id = data.get("id") or str(uuid.uuid4())
        url = data.get("html_url") or f"{base}/incidents/{pd_id}"
        return PageResult(
            team_slug=team.slug,
            team_name=team.name,
            service_id=service_id,
            escalation_policy_id=esc_id,
            pd_incident_id=pd_id,
            pd_incident_url=url,
            escalation_status="notified",
            is_mock=False,
            duplicate=False,
            raw=data,
        )


async def notify_approved_teams(
    db: Session,
    incident: Incident,
    teams: list[SupportTeam],
    *,
    severity: str,
) -> list[PagerDutyNotification]:
    """Page each approved team. Skips teams already notified (duplicate prevention)."""
    created: list[PagerDutyNotification] = []
    for team in teams:
        existing = (
            db.query(PagerDutyNotification)
            .filter(
                PagerDutyNotification.incident_id == incident.id,
                PagerDutyNotification.team_slug == team.slug,
            )
            .first()
        )
        if existing:
            created.append(existing)
            continue
        result = await page_team(incident, team, severity=severity)
        row = PagerDutyNotification(
            incident_id=incident.id,
            occ_incident_id=incident.occ_incident_id,
            servicenow_number=incident.servicenow_number,
            team_slug=result.team_slug,
            team_name=result.team_name,
            pagerduty_service_id=result.service_id,
            pagerduty_escalation_policy_id=result.escalation_policy_id,
            pd_incident_id=result.pd_incident_id,
            pd_incident_url=result.pd_incident_url,
            escalation_status=result.escalation_status,
            notified_at=utc_now(),
            is_mock=result.is_mock,
            raw_json=json.dumps(result.raw) if result.raw else None,
        )
        db.add(row)
        created.append(row)
    db.commit()
    for row in created:
        db.refresh(row)
    return created


def acknowledge_notification(
    db: Session, notification: PagerDutyNotification
) -> PagerDutyNotification:
    notification.acknowledged_at = utc_now()
    notification.escalation_status = "acknowledged"
    db.commit()
    db.refresh(notification)
    return notification
