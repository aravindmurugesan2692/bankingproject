"""Seed realistic MOCK sample incidents and support teams."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Incident, IncidentAnalysis, IncidentPriority, IncidentStatus, SupportTeam


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


SUPPORT_TEAMS: list[dict] = [
    {
        "name": "Application Support",
        "slug": "application-support",
        "description": "Owns business application runtime health and functional defects.",
        "ownership": "Payment Gateway, Mobile Banking SSO, Branch Portal, Notification Service, Core Banking API",
        "responsibilities": "App logs, releases, feature toggles, upstream/downstream API contracts",
        "pagerduty_service_id": "PD_SVC_APP_SUPPORT_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_APP_SUPPORT_PLACEHOLDER",
        "keywords": "application,api,gateway,payment,sso,portal,notification,timeout,500,504",
    },
    {
        "name": "Linux Administration",
        "slug": "linux-administration",
        "description": "Linux OS and host-level operations.",
        "ownership": "Linux VMs and bare-metal hosts supporting banking workloads",
        "responsibilities": "Kernel, systemd, packages, host performance, OS patching",
        "pagerduty_service_id": "PD_SVC_LINUX_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_LINUX_PLACEHOLDER",
        "keywords": "linux,kernel,systemd,host,ssh,cpu,memory",
    },
    {
        "name": "Windows Administration",
        "slug": "windows-administration",
        "description": "Windows Server and Active Directory platform support.",
        "ownership": "Windows Server fleets, Active Directory, GPO",
        "responsibilities": "Windows services, AD auth issues, patch windows",
        "pagerduty_service_id": "PD_SVC_WINDOWS_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_WINDOWS_PLACEHOLDER",
        "keywords": "windows,active directory,gpo,iis",
    },
    {
        "name": "Infrastructure",
        "slug": "infrastructure",
        "description": "Compute, virtualization, and shared platform infrastructure.",
        "ownership": "Hypervisors, shared compute pools, load balancers (infra layer)",
        "responsibilities": "Capacity, host availability, infra change windows",
        "pagerduty_service_id": "PD_SVC_INFRA_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_INFRA_PLACEHOLDER",
        "keywords": "infrastructure,vm,hypervisor,load balancer,capacity",
    },
    {
        "name": "Network",
        "slug": "network",
        "description": "Network connectivity, DNS, firewalls, and routing.",
        "ownership": "DNS, firewalls, WAN/LAN paths, VIP routing",
        "responsibilities": "Latency, packet loss, ACL changes, DNS failures",
        "pagerduty_service_id": "PD_SVC_NETWORK_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_NETWORK_PLACEHOLDER",
        "keywords": "network,dns,firewall,latency,packet,vip,tcp,connectivity",
    },
    {
        "name": "Database",
        "slug": "database",
        "description": "Relational and operational data platforms.",
        "ownership": "Oracle core DB, SQL Server branch DB, Postgres replicas",
        "responsibilities": "Locks, replication lag, query performance, backups",
        "pagerduty_service_id": "PD_SVC_DATABASE_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_DATABASE_PLACEHOLDER",
        "keywords": "database,sql,oracle,postgres,replication,lock,ora-",
    },
    {
        "name": "Kubernetes / Container Platform",
        "slug": "k8s-containers",
        "description": "Kubernetes clusters and container runtime platform.",
        "ownership": "prod/qa k8s clusters, ingress, workloads",
        "responsibilities": "Pods, deployments, HPA, cluster networking, helm releases",
        "pagerduty_service_id": "PD_SVC_K8S_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_K8S_PLACEHOLDER",
        "keywords": "kubernetes,k8s,container,pod,helm,ingress,docker",
    },
    {
        "name": "Storage",
        "slug": "storage",
        "description": "Block/file/object storage platforms.",
        "ownership": "SAN/NAS volumes, object buckets used by banking apps",
        "responsibilities": "Disk pressure, volume mount failures, IOPS saturation",
        "pagerduty_service_id": "PD_SVC_STORAGE_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_STORAGE_PLACEHOLDER",
        "keywords": "storage,disk,nfs,volume,iops,san,nas",
    },
    {
        "name": "Security",
        "slug": "security",
        "description": "Security operations and control validation.",
        "ownership": "Fraud controls, cert stores, security tooling integrations",
        "responsibilities": "Suspicious activity, cert trust, policy violations",
        "pagerduty_service_id": "PD_SVC_SECURITY_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_SECURITY_PLACEHOLDER",
        "keywords": "security,fraud,cert,certificate,tls,breach,mfa",
    },
    {
        "name": "Cloud Operations",
        "slug": "cloud-ops",
        "description": "Public cloud account and platform operations.",
        "ownership": "AWS/Azure landing zones used by OCC workloads",
        "responsibilities": "Cloud quotas, IAM roles, regional service health",
        "pagerduty_service_id": "PD_SVC_CLOUD_PLACEHOLDER",
        "pagerduty_escalation_policy_id": "PD_ESC_CLOUD_PLACEHOLDER",
        "keywords": "cloud,aws,azure,gcp,iam,region,quota",
    },
]


def seed_support_teams(db: Session) -> int:
    """Upsert support team catalog. Returns number of newly inserted rows."""
    inserted = 0
    for item in SUPPORT_TEAMS:
        existing = db.query(SupportTeam).filter(SupportTeam.slug == item["slug"]).first()
        if existing:
            continue
        db.add(
            SupportTeam(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                ownership=item["ownership"],
                responsibilities=item["responsibilities"],
                pagerduty_service_id=item["pagerduty_service_id"],
                pagerduty_escalation_policy_id=item["pagerduty_escalation_policy_id"],
                active=True,
                keywords=item["keywords"],
            )
        )
        inserted += 1
    if inserted:
        db.commit()
    return inserted


def seed_analyses_for_incidents_missing(db: Session) -> int:
    """Ensure every incident has at least one MOCK analysis for a full demo."""
    from app.services.ai_analysis import seed_heuristic_analysis

    inserted = 0
    incidents = db.query(Incident).order_by(Incident.id.asc()).all()
    for incident in incidents:
        has = (
            db.query(IncidentAnalysis)
            .filter(IncidentAnalysis.incident_id == incident.id)
            .count()
        )
        if has:
            continue
        seed_heuristic_analysis(db, incident)
        inserted += 1
    return inserted


def seed_if_empty(db: Session) -> int:
    """Insert MOCK sample incidents when the table is empty. Returns count inserted."""
    teams_inserted = seed_support_teams(db)
    if teams_inserted:
        print(f"Seeded {teams_inserted} support teams")

    existing = db.query(Incident).count()
    if existing > 0:
        analyses = seed_analyses_for_incidents_missing(db)
        if analyses:
            print(f"Seeded {analyses} MOCK analyses for existing incidents")
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
    analyses = seed_analyses_for_incidents_missing(db)
    if analyses:
        print(f"Seeded {analyses} MOCK analyses")
    return len(SAMPLE_INCIDENTS)
