"""Phase 9 RBAC, settings, and secure-error tests."""

from datetime import datetime, timezone


def _payload(**overrides):
    base = {
        "title": "ATM switch latency spike",
        "description": (
            "ATM authorization latency elevated in Production; "
            "customers report intermittent declines."
        ),
        "application_service": "ATM Switch",
        "environment": "Production",
        "business_impact": "Failed ATM withdrawals",
        "users_affected": 2000,
        "issue_start_time": datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc).isoformat(),
        "error_messages": "upstream timeout",
    }
    base.update(overrides)
    return base


def test_settings_never_returns_secrets(client):
    res = client.get("/api/settings")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["secrets_in_frontend"] is False
    # Env var *names* may appear in help notes; secret *values* must not.
    assert "sk-" not in res.text
    assert "Bearer " not in res.text
    for integ in body["integrations"]:
        assert "configured" in integ
        assert isinstance(integ["configured"], bool)
        # Never embed raw credential fields
        assert "api_key" not in integ
        assert "password" not in integ
        assert "client_secret" not in integ
    assert body["mock_mode"] is True


def test_viewer_cannot_approve(client):
    created = client.post("/api/incidents", json=_payload()).json()
    iid = created["incident"]["id"]
    denied = client.post(
        f"/api/approvals/{iid}/approve",
        json={"actor": "Viewer"},
        headers={"X-OCC-User": "Read Only", "X-OCC-Role": "viewer"},
    )
    assert denied.status_code == 403
    assert "permission denied" in denied.json()["detail"].lower()


def test_engineer_can_approve(client):
    created = client.post("/api/incidents", json=_payload(title="Card network flap west")).json()
    iid = created["incident"]["id"]
    ok = client.post(
        f"/api/approvals/{iid}/approve",
        json={"actor": "OCC Engineer"},
        headers={"X-OCC-User": "OCC Engineer", "X-OCC-Role": "occ_engineer"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["incident"]["status"] == "Active"


def test_engineer_cannot_write_force_mocks(client):
    denied = client.patch(
        "/api/settings/force-mocks",
        json={"force_mock_servicenow": True},
        headers={"X-OCC-User": "OCC Engineer", "X-OCC-Role": "occ_engineer"},
    )
    assert denied.status_code == 403


def test_admin_can_set_force_mocks(client):
    ok = client.patch(
        "/api/settings/force-mocks",
        json={
            "force_mock_servicenow": True,
            "force_mock_pagerduty": True,
            "actor": "Admin",
        },
        headers={"X-OCC-User": "OCC Admin", "X-OCC-Role": "occ_administrator"},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["force_mocks"]["force_mock_servicenow"] is True
    assert body["force_mocks"]["force_mock_pagerduty"] is True


def test_whoami_reflects_headers(client):
    me = client.get(
        "/api/settings/me",
        headers={"X-OCC-User": "Ada Admin", "X-OCC-Role": "occ_administrator"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["display_name"] == "Ada Admin"
    assert body["role"] == "occ_administrator"
    assert "settings:write" in body["permissions"]


def test_unhandled_error_is_sanitized(client):
    # 404 path stays generic
    res = client.get("/api/management/incidents/999999")
    assert res.status_code == 404
    assert "traceback" not in res.text.lower()
