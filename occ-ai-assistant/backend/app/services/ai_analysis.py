"""Configurable LLM incident analysis with heuristic MOCK fallback."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import (
    PRIORITY_FROM_P_CODE,
    Incident,
    IncidentAnalysis,
    IncidentStatus,
    SupportTeam,
)

DISCLAIMER = (
    "AI recommendations are hypotheses for OCC review — not confirmed root cause. "
    "Do not page teams or create tickets solely on this output without OCC validation."
)

ANALYSIS_SCHEMA_HINT = """
Return ONLY valid JSON with this shape:
{
  "summary": "string",
  "category": "string",
  "suggested_priority": "P1|P2|P3|P4",
  "business_impact": "string",
  "potential_causes": ["string"],
  "affected_application": "string",
  "recommended_teams": [{"team": "exact team name", "slug": "slug", "reason": "string"}],
  "troubleshooting_steps": ["string"],
  "missing_information": ["string"],
  "next_actions": ["string"],
  "needs_more_info": true/false
}
Never invent employee names. Prefer team names from the provided catalog only.
If evidence is thin, set needs_more_info=true and list missing_information.
"""


def _blob(incident: Incident) -> str:
    parts = [
        incident.title,
        incident.description,
        incident.application_service,
        incident.environment,
        incident.business_impact,
        incident.error_messages or "",
        incident.affected_infrastructure or "",
        incident.additional_observations or "",
    ]
    return " ".join(parts).lower()


def _score_team(team: SupportTeam, text: str) -> int:
    score = 0
    keywords = [k.strip().lower() for k in (team.keywords or "").split(",") if k.strip()]
    for kw in keywords:
        if kw and kw in text:
            score += 2 if len(kw) > 4 else 1
    ownership = (team.ownership or "").lower()
    for token in re.findall(r"[a-z0-9][a-z0-9\-_/ ]{2,}", ownership):
        token = token.strip()
        if len(token) >= 4 and token in text:
            score += 1
    return score


def _infer_priority(incident: Incident, text: str) -> str:
    if incident.users_affected >= 1000 or "critical" in text or "outage" in text:
        return "P1"
    if incident.environment == "Production" and incident.users_affected >= 200:
        return "P2"
    if "timeout" in text or "error" in text or "fail" in text:
        return "P2" if incident.environment == "Production" else "P3"
    if incident.environment == "Development":
        return "P4"
    return "P3"


def _infer_category(text: str) -> str:
    rules = [
        ("authentication|sso|oidc|mfa|login", "Identity / Access"),
        ("database|sql|oracle|postgres|replication", "Data Platform"),
        ("network|dns|firewall|latency|timeout 504", "Network / Connectivity"),
        ("kubernetes|k8s|container|pod|helm", "Container Platform"),
        ("storage|disk|nfs|volume", "Storage"),
        ("security|fraud|breach|cert", "Security"),
        ("cloud|aws|azure|gcp", "Cloud Platform"),
        ("windows|active directory", "Windows Platform"),
        ("linux|kernel|systemd", "Linux Platform"),
        ("payment|gateway|api|application", "Application"),
    ]
    for pattern, label in rules:
        if re.search(pattern, text):
            return label
    return "General Operations"


def heuristic_analysis(
    incident: Incident, teams: list[SupportTeam]
) -> dict[str, Any]:
    text = _blob(incident)
    scored = sorted(
        ((t, _score_team(t, text)) for t in teams if t.active),
        key=lambda x: x[1],
        reverse=True,
    )
    top = [t for t, s in scored if s > 0][:3]
    if not top:
        # Always recommend Application Support as a safe default plus Infrastructure
        defaults = {t.slug: t for t in teams}
        top = [
            defaults[s]
            for s in ("application-support", "infrastructure")
            if s in defaults
        ]

    priority = _infer_priority(incident, text)
    category = _infer_category(text)
    missing: list[str] = []
    if not incident.error_messages:
        missing.append("Exact error messages / stack traces from logs")
    if not incident.affected_infrastructure:
        missing.append("Known affected hosts, clusters, or components")
    if incident.users_affected == 0 and incident.environment == "Production":
        missing.append("Confirmed user-impact count or monitoring signal")
    if len(incident.description.strip()) < 40:
        missing.append("More detailed reproduction steps and timeline")

    needs_more = len(missing) >= 2 or len(incident.description.strip()) < 25

    causes = [
        "Recent change or deployment correlated with issue start time",
        "Dependency timeout or saturation under current load",
        "Configuration drift between expected and observed runtime state",
    ]
    if "cert" in text:
        causes.insert(0, "TLS certificate rotation or trust-store mismatch")
    if "dns" in text or "network" in text:
        causes.insert(0, "DNS or network path degradation")
    if "database" in text or "sql" in text or "ora-" in text:
        causes.insert(0, "Database lock, lag, or resource contention")

    recommended = []
    for team in top:
        reason = (
            f"Ownership/keywords align with reported symptoms "
            f"({team.ownership.split(',')[0].strip()})."
        )
        recommended.append({"team": team.name, "slug": team.slug, "reason": reason})

    steps = [
        "Confirm blast radius via monitoring dashboards for the reported service",
        "Capture recent deploy/config change history around issue start time",
        "Collect representative error logs without PII for the failing path",
        "Validate dependency health (downstream APIs, DB, cache, network)",
    ]
    next_actions = [
        "OCC reviews AI hypotheses with recommended teams (do not treat as root cause)",
        "Gather any missing information listed before escalation",
        "Prepare approval package for ServiceNow / PagerDuty (Phase 3+)",
    ]
    if needs_more:
        next_actions.insert(
            0, "Request additional details from the reporter before paging teams"
        )

    return {
        "summary": (
            f"{incident.application_service} in {incident.environment}: "
            f"{incident.title}. Heuristic analysis suggests {category} with "
            f"suggested priority {priority}."
        ),
        "category": category,
        "suggested_priority": priority,
        "business_impact": incident.business_impact,
        "potential_causes": causes[:4],
        "affected_application": incident.application_service,
        "recommended_teams": recommended,
        "troubleshooting_steps": steps,
        "missing_information": missing
        or ["None identified — still validate with subject-matter experts"],
        "next_actions": next_actions,
        "needs_more_info": needs_more,
    }


async def llm_analysis(
    incident: Incident, teams: list[SupportTeam], settings: Settings
) -> dict[str, Any]:
    catalog = [
        {
            "name": t.name,
            "slug": t.slug,
            "ownership": t.ownership,
            "responsibilities": t.responsibilities,
        }
        for t in teams
        if t.active
    ]
    user_payload = {
        "incident": {
            "title": incident.title,
            "description": incident.description,
            "application_service": incident.application_service,
            "environment": incident.environment,
            "business_impact": incident.business_impact,
            "users_affected": incident.users_affected,
            "issue_start_time": incident.issue_start_time.isoformat(),
            "error_messages": incident.error_messages,
            "affected_infrastructure": incident.affected_infrastructure,
            "additional_observations": incident.additional_observations,
        },
        "support_teams": catalog,
        "instructions": ANALYSIS_SCHEMA_HINT,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an OCC incident triage assistant. Produce structured JSON "
                    "hypotheses only. Never invent employee names. Never claim confirmed "
                    "root cause."
                ),
            },
            {"role": "user", "content": json.dumps(user_payload)},
        ],
    }
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return _normalize_payload(parsed, incident, teams)


def _normalize_payload(
    payload: dict[str, Any], incident: Incident, teams: list[SupportTeam]
) -> dict[str, Any]:
    team_by_name = {t.name.lower(): t for t in teams}
    team_by_slug = {t.slug: t for t in teams}
    recommended_raw = payload.get("recommended_teams") or []
    recommended: list[dict[str, str]] = []
    for item in recommended_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("team") or item.get("name") or "").strip()
        slug = str(item.get("slug") or "").strip()
        reason = str(item.get("reason") or "Aligned with reported symptoms").strip()
        match = team_by_slug.get(slug) or team_by_name.get(name.lower())
        if not match:
            continue
        recommended.append(
            {"team": match.name, "slug": match.slug, "reason": reason or match.description}
        )
    if not recommended:
        # Fall back to heuristic team picks if LLM returned unknown teams
        recommended = heuristic_analysis(incident, teams)["recommended_teams"]

    priority = str(payload.get("suggested_priority") or "P3").upper()
    if priority not in PRIORITY_FROM_P_CODE:
        priority = "P3"

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if value is None or value == "":
            return []
        return [str(value).strip()]

    missing = as_list(payload.get("missing_information"))
    needs = bool(payload.get("needs_more_info")) or len(missing) >= 2

    return {
        "summary": str(payload.get("summary") or incident.title).strip(),
        "category": str(payload.get("category") or "General Operations").strip(),
        "suggested_priority": priority,
        "business_impact": str(
            payload.get("business_impact") or incident.business_impact
        ).strip(),
        "potential_causes": as_list(payload.get("potential_causes"))
        or ["Insufficient evidence — gather logs before concluding"],
        "affected_application": str(
            payload.get("affected_application") or incident.application_service
        ).strip(),
        "recommended_teams": recommended,
        "troubleshooting_steps": as_list(payload.get("troubleshooting_steps"))
        or ["Validate monitoring signals and recent changes"],
        "missing_information": missing
        or ["None identified — still validate with subject-matter experts"],
        "next_actions": as_list(payload.get("next_actions"))
        or ["OCC review of AI hypotheses before escalation"],
        "needs_more_info": needs,
    }


def persist_analysis(
    db: Session,
    incident: Incident,
    payload: dict[str, Any],
    *,
    provider: str,
    model: str,
    is_mock: bool,
    update_incident_status: bool = True,
) -> IncidentAnalysis:
    analysis = IncidentAnalysis(
        incident_id=incident.id,
        summary=payload["summary"],
        category=payload["category"],
        suggested_priority=payload["suggested_priority"],
        business_impact=payload["business_impact"],
        potential_causes=json.dumps(payload["potential_causes"]),
        affected_application=payload["affected_application"],
        recommended_teams=json.dumps(payload["recommended_teams"]),
        troubleshooting_steps=json.dumps(payload["troubleshooting_steps"]),
        missing_information=json.dumps(payload["missing_information"]),
        next_actions=json.dumps(payload["next_actions"]),
        needs_more_info=bool(payload["needs_more_info"]),
        disclaimer=DISCLAIMER,
        provider=provider,
        model=model,
        is_mock=is_mock,
        raw_json=json.dumps(payload),
    )
    db.add(analysis)
    if update_incident_status:
        incident.status = IncidentStatus.ANALYZED.value
        incident.priority = PRIORITY_FROM_P_CODE.get(
            payload["suggested_priority"], incident.priority
        )
    db.commit()
    db.refresh(analysis)
    db.refresh(incident)
    return analysis


def seed_heuristic_analysis(db: Session, incident: Incident) -> IncidentAnalysis:
    """Seed MOCK analysis for demo incidents without forcing status to Analyzed."""
    teams = db.query(SupportTeam).filter(SupportTeam.active.is_(True)).all()
    payload = heuristic_analysis(incident, teams)
    return persist_analysis(
        db,
        incident,
        payload,
        provider="heuristic",
        model="mock-heuristic-v1",
        is_mock=True,
        update_incident_status=False,
    )


async def analyze_incident(db: Session, incident: Incident) -> IncidentAnalysis:
    settings = get_settings()
    teams = db.query(SupportTeam).filter(SupportTeam.active.is_(True)).all()
    if settings.use_live_llm:
        try:
            payload = await llm_analysis(incident, teams, settings)
            return persist_analysis(
                db,
                incident,
                payload,
                provider=settings.llm_provider,
                model=settings.llm_model,
                is_mock=False,
            )
        except Exception as exc:  # noqa: BLE001 — fall back to heuristic
            payload = heuristic_analysis(incident, teams)
            payload["next_actions"] = [
                f"Live LLM call failed ({type(exc).__name__}); used heuristic fallback",
                *payload["next_actions"],
            ]
            return persist_analysis(
                db,
                incident,
                payload,
                provider="heuristic-fallback",
                model="mock-heuristic-v1",
                is_mock=True,
            )

    payload = heuristic_analysis(incident, teams)
    return persist_analysis(
        db,
        incident,
        payload,
        provider="heuristic",
        model="mock-heuristic-v1",
        is_mock=True,
    )
