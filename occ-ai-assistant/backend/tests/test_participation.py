"""Phase 6 participation + timeline tests."""

from datetime import datetime, timezone


def _payload(**overrides):
    base = {
        "title": "ATM switch latency spike",
        "description": (
            "ATM authorization path latency above SLO. Customers seeing slow cash "
            "withdrawals at retail ATMs."
        ),
        "application_service": "ATM Switch",
        "environment": "Production",
        "business_impact": "Slow ATM withdrawals",
        "users_affected": 400,
        "issue_start_time": datetime(2026, 11, 20, 1, 0, tzinfo=timezone.utc).isoformat(),
        "error_messages": "p99 latency 4.2s",
        "affected_infrastructure": "atm-switch-prod",
    }
    base.update(overrides)
    return base


def _approve_and_bridge(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    client.patch(
        f"/api/approvals/{incident_id}",
        json={
            "selected_team_slugs": ["application-support", "network"],
            "working_severity": "P2",
            "actor": "OCC",
        },
    )
    client.post(f"/api/approvals/{incident_id}/approve", json={"actor": "OCC"})
    bridge = client.post(
        f"/api/bridges/incidents/{incident_id}",
        json={"actor": "OCC", "invite": True},
    ).json()
    opened = client.post(
        f"/api/bridges/{bridge['id']}/open",
        json={"actor": "OCC"},
    ).json()
    return created["incident"], opened


def test_mock_attendance_requires_started_at(client):
    created = client.post("/api/incidents", json=_payload()).json()
    incident_id = created["incident"]["id"]
    client.post(f"/api/approvals/{incident_id}/approve", json={"actor": "OCC"})
    bridge = client.post(
        f"/api/bridges/incidents/{incident_id}",
        json={"actor": "OCC", "invite": False},
    ).json()
    # Not opened yet — sync must refuse fabricating timestamps
    blocked = client.post(
        f"/api/bridges/{bridge['id']}/attendance/sync",
        json={"actor": "OCC"},
    )
    assert blocked.status_code == 400


def test_sync_mock_attendance_and_participation_matrix(client):
    incident, bridge = _approve_and_bridge(client)
    synced = client.post(
        f"/api/bridges/{bridge['id']}/attendance/sync",
        json={"actor": "OCC"},
    )
    assert synced.status_code == 200, synced.text
    rows = synced.json()
    assert len(rows) >= 1
    for row in rows:
        assert row["is_mock"] is True
        assert row["source"] == "mock_sample"
        assert row["event_kind"] == "teams_join"
        assert row["joined_at"]
        assert "MOCK" in (row["notes"] or "").upper()

    matrix = client.get(f"/api/incidents/{incident['id']}/participation").json()
    assert any(r["pd_notified"] for r in matrix)
    assert any(r["teams_joined"] for r in matrix)

    # Confirm one attendance
    confirmed = client.post(
        f"/api/attendance/{rows[0]['id']}/confirm",
        json={"actor": "OCC"},
    ).json()
    assert confirmed["event_kind"] == "attendance_confirmed"
    assert confirmed["verification_status"] == "confirmed"


def test_timeline_distinguishes_event_types(client):
    incident, bridge = _approve_and_bridge(client)
    client.post(
        f"/api/bridges/{bridge['id']}/attendance/sync",
        json={"actor": "OCC"},
    )
    # Ack a PD notification
    notes = client.get("/api/pagerduty/notifications").json()
    mine = [n for n in notes if n["incident_id"] == incident["id"]]
    assert mine
    client.post(f"/api/pagerduty/notifications/{mine[0]['id']}/acknowledge")

    timeline = client.get(f"/api/timeline/incidents/{incident['id']}").json()
    types = {e["event_type"] for e in timeline}
    assert "pd_notify" in types
    assert "pd_ack" in types
    assert "bridge_create" in types or "bridge_open" in types
    assert "teams_join" in types
    # All derived events have real occurred_at
    assert all(e["occurred_at"] for e in timeline)


def test_manual_timeline_edit_audited(client):
    incident, _bridge = _approve_and_bridge(client)
    created = client.post(
        f"/api/timeline/incidents/{incident['id']}",
        json={
            "occurred_at": datetime(2026, 11, 20, 2, 30, tzinfo=timezone.utc).isoformat(),
            "detail": "OCC noted intermittent ATM timeouts continuing",
            "actor": "OCC Editor",
        },
    )
    assert created.status_code == 200, created.text
    event = created.json()
    assert event["event_type"] == "manual"
    assert event["editable"] is True

    edited = client.patch(
        f"/api/timeline/events/{event['id']}",
        json={
            "actor": "OCC Editor",
            "detail": "OCC noted intermittent ATM timeouts — clarifying region East",
            "verification_status": "verified",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["verification_status"] in {"verified", "edited"}
    audits = client.get(f"/api/timeline/events/{event['id']}/audits").json()
    assert len(audits) >= 1


def test_manual_attendance_requires_joined_at(client):
    _incident, bridge = _approve_and_bridge(client)
    bad = client.post(
        f"/api/bridges/{bridge['id']}/attendance",
        json={"display_name": "Someone", "actor": "OCC"},
    )
    assert bad.status_code == 422
