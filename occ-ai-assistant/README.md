# OCC AI Assistant — Phase 3

Full runnable OCC slice through **approvals + ServiceNow (mock by default)**.

Phases included: **1 dashboard/initiate**, **2 AI analysis/teams**, **3 OCC approval + ServiceNow**.

Banking Java app and `occ-bridge/` are untouched.

## Workflow

1. **Initiate Incident** → persist + auto AI analysis  
2. **Incident Analysis** → review hypotheses / recommended teams  
3. **Incident Approvals** → modify severity / teams / description → **Approve** or **Reject**  
4. On **Approve only** → create ServiceNow incident (MOCK unless live credentials + `MOCK_MODE=false`)  
5. Audit trail stores approving user, timestamp, approved teams  

PagerDuty paging and Teams bridges are **not** started (Phases 4–5).

## Quick start

```bash
# Backend
cd occ-ai-assistant/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (other terminal)
cd occ-ai-assistant/frontend
npm install && npm run dev
# → http://localhost:5173
```

### Tests

```bash
cd occ-ai-assistant/backend && source .venv/bin/activate && pytest -q
```

## ServiceNow behaviour

| Condition | Result |
|-----------|--------|
| `MOCK_MODE=true` (default) or SN not configured | MOCK number + sys_id; labeled mock |
| `MOCK_MODE=false` + instance/auth configured | Live `POST /api/now/table/incident` with retries |
| Incident already has `servicenow_sys_id` | Duplicate prevention — return existing |

Env vars: see `.env.example` (`SERVICENOW_*`).

## Key APIs (Phase 3)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/approvals` | Approval queue packets |
| GET | `/api/approvals/{id}` | Packet: incident + analysis + SN preview + PD placeholders + audit |
| PATCH | `/api/approvals/{id}` | Draft: severity / description / teams |
| POST | `/api/approvals/{id}/approve` | Approve + create ServiceNow |
| POST | `/api/approvals/{id}/reject` | Reject with reason (no SN) |

## Credentials

- **Demo:** none  
- **Optional LLM:** `OPENAI_API_KEY` + `MOCK_MODE=false`  
- **Optional live ServiceNow:** instance URL + username/password (or client id/secret) + `MOCK_MODE=false`

## Waiting for approval

Do **not** start Phase 4 (PagerDuty) until the user approves Phase 3.
