"""Seed realistic MOCK sample incidents for the dashboard."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Incident, IncidentPriority, IncidentStatus


def _occ_id(n: int) -> str:
    return f"OCC-{2026000 + n}"


SAMPLE_INCIDENTS: list[dict] = [
    {
        "n": 1,
        "title": "Payment Gateway timeout spikes in Production",
        "description": (
            "Users report intermittent 504 timeouts when submitting card payments. "
            "Latency spiked above 8s starting around 09:15 UTC."
        ),
        "application_service": "Payment Gateway",
        "environment": "Production",
        "business_impact": "Checkout failures for online banking and card payments",
        "users_affected": 4200,
        "hours_ago": 3,
        "error_messages": "Gateway Timeout 504; upstream connect error",
        "affected_infrastructure": "pgw-prod-east-1, redis-session-cluster",
        "additional_observations": "Correlation with recent cert rotation",
        "status": IncidentStatus.ACTIVE.value,
        "priority": IncidentPriority.CRITICAL.value,
        "ack_minutes": 6,
        "resolution_minutes": None,
        "bridge_active": True,
        "created_by": "A. Chen",
    },
    {
        "n": 2,
        "title": "Mobile app login failures (SSO)",
        "description": (
            "Mobile banking SSO redirect loops after MFA challenge. "
            "Affects iOS 17+ clients primarily."
        ),
        "application_service": "Mobile Banking SSO",
        "environment": "Production",
        "business_impact": "Customers unable to authenticate into mobile app",
        "users_affected": 1800,
        "hours_ago": 5,
        "error_messages": "OIDC invalid_grant; nonce mismatch",
        "affected_infrastructure": "idp-prod, mobile-api-gw",
        "additional_observations": None,
        "status": IncidentStatus.PENDING_APPROVAL.value,
        "priority": IncidentPriority.HIGH.value,
        "ack_minutes": 12,
        "resolution_minutes": None,
        "bridge_active": False,
        "created_by": "M. Okonkwo",
    },
    {
        "n": 3,
        "title": "Wire transfer batch job stalled",
        "description": "Nightly wire batch JOB-WIRE-042 hung at 02:10; backlog of 312 transfers.",
        "application_service": "Wire Transfer Engine",
        "environment": "Production",
        "business_impact": "Delayed corporate wire settlements",
        "users_affected": 312,
        "hours_ago": 10,
        "error_messages": "ORA-00054 resource busy",
        "affected_infrastructure": "wire-batch-worker-03, oracle-core-db",
        "additional_observations": "Lock held by long-running report session",
        "status": IncidentStatus.ACTIVE.value,
        "priority": IncidentPriority.HIGH.value,
        "ack_minutes": 9,
        "resolution_minutes": None,
        "bridge_active": True,
        "created_by": "S. Patel",
    },
    {
        "n": 4,
        "title": "QA environment ATM simulator unreachable",
        "description": "ATM simulator hosts in QA cannot reach the ISO8583 gateway.",
        "application_service": "ATM Simulator",
        "environment": "QA",
        "business_impact": "Blocks regression testing for ATM release train",
        "users_affected": 0,
        "hours_ago": 26,
        "error_messages": "Connection refused tcp/5000",
        "affected_infrastructure": "atm-sim-qa-01",
        "additional_observations": None,
        "status": IncidentStatus.RESOLVED.value,
        "priority": IncidentPriority.MEDIUM.value,
        "ack_minutes": 18,
        "resolution_minutes": 95,
        "bridge_active": False,
        "created_by": "J. Rivera",
    },
    {
        "n": 5,
        "title": "Core ledger replication lag",
        "description": "Replica lag exceeded 120s on core-ledger-ro-2 during peak.",
        "application_service": "Core Ledger",
        "environment": "Production",
        "business_impact": "Stale balances on read-only reporting dashboards",
        "users_affected": 650,
        "hours_ago": 48,
        "error_messages": "replication lag alert: 142s",
        "affected_infrastructure": "core-ledger-ro-2",
        "additional_observations": "Resolved after vacuum and parameter tune",
        "status": IncidentStatus.RESOLVED.value,
        "priority": IncidentPriority.CRITICAL.value,
        "ack_minutes": 4,
        "resolution_minutes": 140,
        "bridge_active": False,
        "created_by": "A. Chen",
    },
    {
        "n": 6,
        "title": "Dev sandbox email relay bounce storm",
        "description": "Outbound notification emails bouncing with 550 mailbox unavailable.",
        "application_service": "Notification Service",
        "environment": "Development",
        "business_impact": "Dev testing of customer alerts blocked",
        "users_affected": 25,
        "hours_ago": 8,
        "error_messages": "550 5.1.1 User unknown",
        "affected_infrastructure": "smtp-dev-relay",
        "additional_observations": "Misconfigured allowlist after vendor change",
        "status": IncidentStatus.ACTIVE.value,
        "priority": IncidentPriority.LOW.value,
        "ack_minutes": 30,
        "resolution_minutes": None,
        "bridge_active": False,
        "created_by": "T. Nguyen",
    },
    {
        "n": 7,
        "title": "Fraud detection rule engine elevated false positives",
        "description": "Rule FRD-221 marking legitimate card-not-present as high risk.",
        "application_service": "Fraud Detection",
        "environment": "Production",
        "business_impact": "Legitimate transactions declined; call-center volume up 22%",
        "users_affected": 940,
        "hours_ago": 2,
        "error_messages": None,
        "affected_infrastructure": "fraud-rules-prod",
        "additional_observations": "Pending approval to roll back rule pack v3.4.1",
        "status": IncidentStatus.PENDING_APPROVAL.value,
        "priority": IncidentPriority.CRITICAL.value,
        "ack_minutes": 5,
        "resolution_minutes": None,
        "bridge_active": True,
        "created_by": "M. Okonkwo",
    },
    {
        "n": 8,
        "title": "Branch portal slow page loads",
        "description": "Branch teller portal TTFB > 4s for account lookup screens.",
        "application_service": "Branch Portal",
        "environment": "Production",
        "business_impact": "Longer customer wait times at branches",
        "users_affected": 210,
        "hours_ago": 72,
        "error_messages": "APM: slow SQL on ACCOUNT_LOOKUP",
        "affected_infrastructure": "branch-api, sql-branch-01",
        "additional_observations": None,
        "status": IncidentStatus.CLOSED.value,
        "priority": IncidentPriority.MEDIUM.value,
        "ack_minutes": 15,
        "resolution_minutes": 210,
        "bridge_active": False,
        "created_by": "S. Patel",
    },
]


def seed_if_empty(db: Session) -> int:
    """Insert MOCK sample incidents when the table is empty. Returns count inserted."""
    existing = db.query(Incident).count()
    if existing > 0:
        return 0

    now = datetime.now(UTC).replace(tzinfo=None)
    for item in SAMPLE_INCIDENTS:
        start = now - timedelta(hours=item["hours_ago"])
        incident = Incident(
            occ_incident_id=_occ_id(item["n"]),
            title=item["title"],
            description=item["description"],
            application_service=item["application_service"],
            environment=item["environment"],
            business_impact=item["business_impact"],
            users_affected=item["users_affected"],
            issue_start_time=start,
            error_messages=item["error_messages"],
            affected_infrastructure=item["affected_infrastructure"],
            additional_observations=item["additional_observations"],
            status=item["status"],
            priority=item["priority"],
            is_mock=True,
            ack_minutes=item["ack_minutes"],
            resolution_minutes=item["resolution_minutes"],
            bridge_active=item["bridge_active"],
            created_by=item["created_by"],
            created_at=start + timedelta(minutes=5),
            updated_at=now,
        )
        db.add(incident)

    db.commit()
    return len(SAMPLE_INCIDENTS)
