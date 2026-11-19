"""Unit/smoke tests for create-incident API."""

from datetime import datetime, timezone


def _valid_payload(**overrides):
    base = {
        "title": "ATM network outage at Region West",
        "description": "Multiple ATMs offline across Region West branches since morning.",
        "application_service": "ATM Network",
        "environment": "Production",
        "business_impact": "Customers cannot withdraw cash at affected branches",
        "users_affected": 150,
        "issue_start_time": datetime(2026, 11, 19, 8, 30, tzinfo=timezone.utc).isoformat(),
        "error_messages": "HOST_UNREACHABLE",
        "affected_infrastructure": "atm-switch-west",
        "additional_observations": "Vendor ticket opened",
        "created_by": "Test Operator",
    }
    base.update(overrides)
    return base


def test_create_incident_success(client):
    response = client.post("/api/incidents", json=_valid_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    data = body["incident"]
    assert data["title"] == "ATM network outage at Region West"
    assert data["environment"] == "Production"
    assert data["users_affected"] == 150
    assert data["status"] == "Analyzed"
    assert data["occ_incident_id"].startswith("OCC-")
    assert data["is_mock"] is False
    assert data["id"] >= 1
    analysis = body["analysis"]
    assert analysis is not None
    assert analysis["suggested_priority"] in {"P1", "P2", "P3", "P4"}
    assert analysis["recommended_teams"]
    assert "not confirmed root cause" in analysis["disclaimer"].lower()


def test_create_incident_persists_and_listable(client):
    created = client.post("/api/incidents", json=_valid_payload()).json()["incident"]
    listed = client.get("/api/incidents")
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()]
    assert created["id"] in ids


def test_create_incident_rejects_missing_mandatory_title(client):
    payload = _valid_payload()
    del payload["title"]
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 422


def test_create_incident_rejects_blank_description(client):
    response = client.post("/api/incidents", json=_valid_payload(description="   "))
    assert response.status_code == 422


def test_create_incident_rejects_invalid_environment(client):
    response = client.post(
        "/api/incidents",
        json=_valid_payload(environment="Staging"),
    )
    assert response.status_code == 422


def test_create_incident_allows_optional_fields_null(client):
    payload = _valid_payload(
        error_messages=None,
        affected_infrastructure=None,
        additional_observations=None,
    )
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()["incident"]
    assert data["error_messages"] is None
    assert data["affected_infrastructure"] is None


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mock_mode"] is True


def test_dashboard_summary(client):
    client.post("/api/incidents", json=_valid_payload())
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_incidents"] >= 1
    assert body["data_label"] == "MOCK DATA"
