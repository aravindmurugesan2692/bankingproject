# OCC AI Assistant — Phase 4

Full runnable OCC slice through **PagerDuty notifications** (MOCK by default).

Phases included: 1 dashboard/initiate → 2 AI analysis → 3 approvals + ServiceNow → **4 PagerDuty**.

Banking Java app and `occ-bridge/` are untouched.

## Workflow

1. Initiate incident → auto AI analysis  
2. OCC Approvals → edit severity/teams/description  
3. **Approve** → ServiceNow create → **PagerDuty page approved teams**  
4. Track notify/ack timestamps, escalation status, PD id/URL  
5. Linked IDs: OCC + ServiceNow + PagerDuty  

**Never pages without explicit OCC approval.** Reject creates no SN and no PD pages.

Teams bridges are Phase 5 (not started).

## Quick start

```bash
# Backend
cd occ-ai-assistant/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd occ-ai-assistant/frontend
npm install && npm run dev
# → http://localhost:5173
```

### Tests

```bash
cd occ-ai-assistant/backend && source .venv/bin/activate && pytest -q
```

## PagerDuty behaviour

| Condition | Result |
|-----------|--------|
| Not OCC-approved | Notify APIs return 400 |
| `MOCK_MODE=true` or no `PAGERDUTY_API_KEY` | MOCK PD id/URL per team |
| Live key + `MOCK_MODE=false` | Incidents API create (placeholder service IDs still mock) |
| Re-notify | Idempotent — existing team pages reused |

Env: `PAGERDUTY_API_KEY`, `PAGERDUTY_API_URL` (see `.env.example`).

## Key APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/pagerduty/notifications` | All PD pages |
| GET | `/api/pagerduty/incidents/{id}/notifications` | Pages for one incident |
| POST | `/api/pagerduty/notifications/{id}/acknowledge` | Record acknowledgement |
| POST | `/api/pagerduty/incidents/{id}/notify` | Idempotent re-page (approved only) |
| POST | `/api/approvals/{id}/approve` | Approve → SN → PD pages |

## Credentials

- Demo: none  
- Optional live PD: `PAGERDUTY_API_KEY` (+ `MOCK_MODE=false`)  
- Optional live SN / LLM: see earlier phases  

## Waiting for approval

Do **not** start Phase 5 (Teams bridges) until the user approves Phase 4.
