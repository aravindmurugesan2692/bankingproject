"""Phase 8 closure automation + history / reporting tests."""

from datetime import datetime, timedelta, timezone


def _payload(**overrides):
    base = {
        "title": "Card payments intermittent 504",
        "description": (
            "Users report intermittent 504 timeouts when submitting card payments. "
            "Edge gateway metrics elevated."
        ),
        "application_service": "Payment Gateway",
        "environment": "Production",
        "business_impact": "Failed card payments",
        "users_affected": 800,
        "issue_start_time": datetime(2026, 11, 20, 4, 0, tzinfo=timezone.utc).isoformat(),
        "error_messages": "HTTP 504 upstream timeout",
        "affected_infrastructure": "pgw-prod-east",
    }
    base.update(overrides)
    return base


def _approve(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    approved = client.post(
        f"/api/approvals/{incident_id}/approve",
        json={"actor": "OCC"},
    )
    assert approved.status_code == 200, approved.text
    return approved.json()["incident"]


def test_history_and_metrics(client):
    incident = _approve(client)
    hist = client.get("/api/management/history")
    assert hist.status_code == 200, hist.text
    body = hist.json()
    assert body["total"] >= 1
    assert any(i["id"] == incident["id"] for i in body["items"])
    assert "data_label" in body

    filtered = client.get(
        "/api/management/history",
        params={"q": incident["occ_incident_id"], "status": "Active"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1

    metrics = client.get("/api/management/metrics")
    assert metrics.status_code == 200, metrics.text
    m = metrics.json()
    assert m["total_incidents"] >= 1
    assert "by_category" in m
    assert "volume_by_application" in m
    assert m["data_label"]


def test_closure_requires_occ_approve_before_sn_pd(client):
    incident = _approve(client)
    iid = incident["id"]

    # Cannot close before Active
    # Already Active after approve.

    opened = client.post(
        f"/api/management/incidents/{iid}/closure",
        json={"actor": "OCC"},
    )
    assert opened.status_code == 200, opened.text
    closure = opened.json()
    assert closure["status"] == "draft"
    assert closure["rca_status"] == "unconfirmed"

    # Submit without restored_at fails
    blocked = client.post(
        f"/api/management/closures/{closure['id']}/submit",
        json={"actor": "OCC"},
    )
    assert blocked.status_code == 400

    restored = (
        datetime(2026, 11, 20, 4, 0, tzinfo=timezone.utc) + timedelta(hours=2)
    ).isoformat()
    patched = client.patch(
        f"/api/management/closures/{closure['id']}",
        json={
            "restored_at": restored,
            "final_summary": "Gateway cert renewed; payments restored.",
            "team_notes": "Network + App Support coordinated cert rollout.",
            "remediation_notes": "Rotated edge cert; flushed CDN cache.",
            "rca_status": "unconfirmed",
            "rca_statement": "",
            "actor": "OCC",
        },
    )
    assert patched.status_code == 200, patched.text

    # Approve directly from draft must fail — never AI/OCC-skip
    early = client.post(
        f"/api/management/closures/{closure['id']}/approve",
        json={"actor": "OCC"},
    )
    assert early.status_code == 400
    assert "OCC approval required" in early.json()["detail"] or "pending" in early.json()[
        "detail"
    ].lower() or "draft" in early.json()["detail"].lower() or "cannot close" in early.json()[
        "detail"
    ].lower()

    submitted = client.post(
        f"/api/management/closures/{closure['id']}/submit",
        json={"actor": "OCC"},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "pending_occ"

    approved = client.post(
        f"/api/management/closures/{closure['id']}/approve",
        json={"actor": "OCC Lead", "close_fully": True},
    )
    assert approved.status_code == 200, approved.text
    done = approved.json()
    assert done["status"] == "completed"
    assert done["servicenow_resolved"] is True
    assert done["pagerduty_resolved"] is True
    assert done["approved_by"] == "OCC Lead"

    detail = client.get(f"/api/management/incidents/{iid}")
    assert detail.status_code == 200
    d = detail.json()
    assert d["incident"]["status"] == "Closed"
    assert d["incident"]["restored_at"] is not None
    assert d["incident"]["rca_status"] == "unconfirmed"
    assert d["closure"]["status"] == "completed"


def test_confirmed_rca_requires_statement(client):
    incident = _approve(client)
    opened = client.post(
        f"/api/management/incidents/{incident['id']}/closure",
        json={"actor": "OCC"},
    ).json()
    restored = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc).isoformat()
    client.patch(
        f"/api/management/closures/{opened['id']}",
        json={
            "restored_at": restored,
            "final_summary": "Resolved after DB failover.",
            "rca_status": "confirmed",
            "rca_statement": "",
            "actor": "OCC",
        },
    )
    bad = client.post(
        f"/api/management/closures/{opened['id']}/submit",
        json={"actor": "OCC"},
    )
    assert bad.status_code == 400

    client.patch(
        f"/api/management/closures/{opened['id']}",
        json={
            "rca_statement": "Primary DB node disk full; failover restored service.",
            "actor": "OCC",
        },
    )
    ok = client.post(
        f"/api/management/closures/{opened['id']}/submit",
        json={"actor": "OCC"},
    )
    assert ok.status_code == 200


def test_reject_returns_to_draft_path(client):
    incident = _approve(client)
    opened = client.post(
        f"/api/management/incidents/{incident['id']}/closure",
        json={"actor": "OCC"},
    ).json()
    restored = datetime(2026, 11, 20, 7, 0, tzinfo=timezone.utc).isoformat()
    client.patch(
        f"/api/management/closures/{opened['id']}",
        json={
            "restored_at": restored,
            "final_summary": "Temporary fix applied.",
            "actor": "OCC",
        },
    )
    client.post(
        f"/api/management/closures/{opened['id']}/submit",
        json={"actor": "OCC"},
    )
    rejected = client.post(
        f"/api/management/closures/{opened['id']}/reject",
        json={"actor": "OCC Lead", "reason": "Need clearer remediation notes"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    # Edit after reject reopens draft
    patched = client.patch(
        f"/api/management/closures/{opened['id']}",
        json={"remediation_notes": "Patched and verified", "actor": "OCC"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "draft"


def test_closure_blocked_for_new_incident(client):
    created = client.post("/api/incidents", json=_payload(title="SSO login failures widespread")).json()
    iid = created["incident"]["id"]
    # May already be Analyzed after create — still not Active
    bad = client.post(
        f"/api/management/incidents/{iid}/closure",
        json={"actor": "OCC"},
    )
    assert bad.status_code == 400
