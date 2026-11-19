"""Phase 4 PagerDuty notification tests."""

from datetime import datetime, timezone


def _payload(**overrides):
    base = {
        "title": "Database replication lag critical",
        "description": (
            "Core ledger replica lag exceeded 120s during peak. Read dashboards showing "
            "stale balances for retail customers."
        ),
        "application_service": "Core Ledger",
        "environment": "Production",
        "business_impact": "Stale balances on reporting",
        "users_affected": 900,
        "issue_start_time": datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc).isoformat(),
        "error_messages": "replication lag alert: 142s",
        "affected_infrastructure": "core-ledger-ro-2",
    }
    base.update(overrides)
    return base


def test_no_pagerduty_before_approval(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    blocked = client.post(f"/api/pagerduty/incidents/{incident_id}/notify")
    assert blocked.status_code == 400
    assert "approval" in blocked.json()["detail"].lower()
    listed = client.get("/api/pagerduty/notifications")
    assert listed.status_code == 200
    assert all(n["incident_id"] != incident_id for n in listed.json())


def test_approve_creates_mock_pagerduty_pages(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    # Ensure at least application-support + database selected
    client.patch(
        f"/api/approvals/{incident_id}",
        json={
            "selected_team_slugs": ["application-support", "database"],
            "working_severity": "P1",
            "actor": "OCC Approver",
        },
    )
    approved = client.post(
        f"/api/approvals/{incident_id}/approve",
        json={"actor": "OCC Approver"},
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["incident"]["status"] == "Active"
    assert body["servicenow_number"]
    assert body["pagerduty_notifications"]
    assert len(body["pagerduty_notifications"]) >= 1
    for note in body["pagerduty_notifications"]:
        assert note["pd_incident_id"]
        assert note["pd_incident_url"]
        assert note["notified_at"]
        assert note["escalation_status"] == "notified"
        assert note["is_mock"] is True
        assert note["occ_incident_id"]
        assert note["servicenow_number"] == body["servicenow_number"]
    actions = {e["action"] for e in body["audit_trail"]}
    assert "pagerduty_notify" in actions


def test_acknowledge_notification(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    approved = client.post(
        f"/api/approvals/{incident_id}/approve",
        json={"actor": "OCC Approver"},
    ).json()
    note_id = approved["pagerduty_notifications"][0]["id"]
    ack = client.post(f"/api/pagerduty/notifications/{note_id}/acknowledge")
    assert ack.status_code == 200
    assert ack.json()["escalation_status"] == "acknowledged"
    assert ack.json()["acknowledged_at"] is not None


def test_duplicate_notify_is_idempotent(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    first = client.post(
        f"/api/approvals/{incident_id}/approve",
        json={"actor": "OCC Approver"},
    ).json()["pagerduty_notifications"]
    second = client.post(f"/api/pagerduty/incidents/{incident_id}/notify").json()
    assert {n["pd_incident_id"] for n in first} == {n["pd_incident_id"] for n in second}


def test_reject_does_not_page(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    client.post(
        f"/api/approvals/{incident_id}/reject",
        json={"actor": "OCC Approver", "rejection_reason": "False alarm"},
    )
    notes = client.get("/api/pagerduty/notifications").json()
    assert all(n["incident_id"] != incident_id for n in notes)
