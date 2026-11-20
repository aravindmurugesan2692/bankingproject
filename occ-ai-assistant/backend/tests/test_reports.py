"""Phase 7 AI bridge assistant + ServiceNow work-note tests."""

from datetime import datetime, timezone


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


def test_ai_requires_approved_notes(client):
    incident = _approve(client)
    blocked = client.post(
        f"/api/incidents/{incident['id']}/bridge-updates/generate",
        json={"actor": "OCC"},
    )
    assert blocked.status_code == 400


def test_generate_from_approved_notes_and_worknote_flow(client):
    incident = _approve(client)
    note = client.post(
        f"/api/incidents/{incident['id']}/bridge-notes",
        json={
            "title": "Bridge excerpt",
            "note_type": "transcript_excerpt",
            "content": (
                "Network suspects possible certificate mismatch on pgw-prod-east. "
                "App Support will check deployment timestamps next. "
                "What additional evidence is needed from edge logs?"
            ),
            "approve_now": True,
            "actor": "OCC",
            "occurred_at": datetime(2026, 11, 20, 4, 20, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert note.status_code == 200, note.text
    assert note.json()["status"] == "approved"

    update = client.post(
        f"/api/incidents/{incident['id']}/bridge-updates/generate",
        json={"actor": "OCC"},
    )
    assert update.status_code == 200, update.text
    body = update.json()
    assert body["root_cause_status"] in {"unconfirmed", "insufficient_evidence"}
    assert "not confirmed root cause" in body["disclaimer"].lower()
    assert body["source_note_ids"]
    assert body["key_points"]

    preview = client.post(
        f"/api/bridge-updates/{body['id']}/work-notes/preview",
        json={"actor": "OCC"},
    )
    assert preview.status_code == 200, preview.text
    draft = preview.json()
    assert draft["status"] == "preview"
    assert "UNCONFIRMED" in draft["content"].upper()
    assert draft["servicenow_number"]

    # Post without approve must fail
    blocked = client.post(
        f"/api/work-notes/{draft['id']}/post",
        json={"actor": "OCC"},
    )
    assert blocked.status_code == 400

    approved = client.post(
        f"/api/work-notes/{draft['id']}/approve",
        json={"actor": "OCC"},
    ).json()
    assert approved["status"] == "approved"

    posted = client.post(
        f"/api/work-notes/{draft['id']}/post",
        json={"actor": "OCC"},
    )
    assert posted.status_code == 200, posted.text
    assert posted.json()["draft"]["status"] == "posted"
    assert posted.json()["is_mock"] is True
    assert posted.json()["draft"]["posted_at"]


def test_worknote_dedupe(client):
    incident = _approve(client)
    client.post(
        f"/api/incidents/{incident['id']}/bridge-notes",
        json={
            "content": "Suspect cert rotation issue. Will verify edge cert expiry next.",
            "approve_now": True,
            "actor": "OCC",
        },
    )
    update = client.post(
        f"/api/incidents/{incident['id']}/bridge-updates/generate",
        json={"actor": "OCC"},
    ).json()
    d1 = client.post(
        f"/api/bridge-updates/{update['id']}/work-notes/preview",
        json={"actor": "OCC"},
    ).json()
    client.post(f"/api/work-notes/{d1['id']}/approve", json={"actor": "OCC"})
    client.post(f"/api/work-notes/{d1['id']}/post", json={"actor": "OCC"})

    d2 = client.post(
        f"/api/bridge-updates/{update['id']}/work-notes/preview",
        json={"actor": "OCC"},
    ).json()
    client.post(f"/api/work-notes/{d2['id']}/approve", json={"actor": "OCC"})
    second = client.post(
        f"/api/work-notes/{d2['id']}/post",
        json={"actor": "OCC"},
    ).json()
    assert second["duplicate"] is True
    assert second["draft"]["status"] == "skipped_duplicate"
