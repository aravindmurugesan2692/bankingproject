"""Phase 5 Teams bridge tests."""

from datetime import datetime, timezone


def _payload(**overrides):
    base = {
        "title": "Mobile SSO outage on retail apps",
        "description": (
            "SSO broker returning 503 for mobile banking login. Customers cannot "
            "authenticate to retail apps during peak."
        ),
        "application_service": "Mobile Banking",
        "environment": "Production",
        "business_impact": "Login failures",
        "users_affected": 1200,
        "issue_start_time": datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc).isoformat(),
        "error_messages": "HTTP 503 from sso-broker",
        "affected_infrastructure": "sso-broker-prod",
    }
    base.update(overrides)
    return base


def _approve(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    client.patch(
        f"/api/approvals/{incident_id}",
        json={
            "selected_team_slugs": ["application-support", "security"],
            "working_severity": "P1",
            "actor": "OCC Approver",
        },
    )
    approved = client.post(
        f"/api/approvals/{incident_id}/approve",
        json={"actor": "OCC Approver"},
    )
    assert approved.status_code == 200, approved.text
    return approved.json()["incident"]


def test_no_bridge_before_approval(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    blocked = client.post(
        f"/api/bridges/incidents/{incident_id}",
        json={"actor": "OCC"},
    )
    assert blocked.status_code == 400
    assert "approv" in blocked.json()["detail"].lower()


def test_create_mock_bridge_after_approve(client):
    incident = _approve(client)
    response = client.post(
        f"/api/bridges/incidents/{incident['id']}",
        json={"actor": "OCC Bridge", "invite": True},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["occ_incident_id"] == incident["occ_incident_id"]
    assert body["meeting_id"]
    assert body["meeting_url"]
    assert body["status"] == "created"
    assert body["started_at"] is None  # not fabricated
    assert body["ended_at"] is None
    assert body["is_mock"] is True
    assert body["invited_count"] >= 1
    assert body["invited_at"] is not None
    assert body["bridge_code"].startswith("STS")


def test_open_and_end_set_real_timestamps(client):
    incident = _approve(client)
    created = client.post(
        f"/api/bridges/incidents/{incident['id']}",
        json={"actor": "OCC", "invite": False},
    ).json()
    opened = client.post(
        f"/api/bridges/{created['id']}/open",
        json={"actor": "OCC"},
    ).json()
    assert opened["status"] == "open"
    assert opened["started_at"] is not None
    assert opened["ended_at"] is None

    ended = client.post(
        f"/api/bridges/{created['id']}/end",
        json={"actor": "OCC"},
    ).json()
    assert ended["status"] == "ended"
    assert ended["ended_at"] is not None
    assert ended["started_at"] == opened["started_at"]


def test_duplicate_create_returns_existing(client):
    incident = _approve(client)
    first = client.post(
        f"/api/bridges/incidents/{incident['id']}",
        json={"actor": "OCC"},
    ).json()
    second = client.post(
        f"/api/bridges/incidents/{incident['id']}",
        json={"actor": "OCC"},
    ).json()
    assert first["id"] == second["id"]
    assert first["meeting_id"] == second["meeting_id"]


def test_dashboard_lists_bridges(client):
    incident = _approve(client)
    client.post(
        f"/api/bridges/incidents/{incident['id']}",
        json={"actor": "OCC"},
    )
    dash = client.get("/api/dashboard").json()
    assert dash["teams_bridges"]
    assert any(b["occ_incident_id"] == incident["occ_incident_id"] for b in dash["teams_bridges"])
    assert any(b["incident_id"] == incident["occ_incident_id"] for b in dash["active_bridges"])
