# OCC AI Assistant — Phase 5

Full runnable OCC slice through **Microsoft Teams bridge automation** (MOCK by default).

Phases included: 1 dashboard/initiate → 2 AI analysis → 3 approvals + ServiceNow → 4 PagerDuty → **5 Teams bridges**.

Banking Java app and `occ-bridge/` are untouched.

## Workflow

1. Initiate incident → auto AI analysis  
2. OCC Approvals → edit severity/teams/description  
3. **Approve** → ServiceNow create → PagerDuty page approved teams  
4. **Teams Bridge Management** → create/associate meeting, invite approved responders, open/end  
5. Store meeting ID/URL, create/start/end times (only when actions run), status, OCC linkage  

**No real-time attendance** (Phase 6). Start/end times are not fabricated.

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

## Teams bridge behaviour

| Condition | Result |
|-----------|--------|
| Incident not Approved/Active | Create returns 400 |
| `MOCK_MODE=true` or missing Graph creds | MOCK meeting id/URL |
| Live Graph configured + `MOCK_MODE=false` | Attempts Graph create; falls back to MOCK on failure |
| Open / End | Sets `started_at` / `ended_at` to the real action time only |
| Invite | MOCK invites to approved team responders |

Env: `MICROSOFT_TENANT_ID`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` (see `.env.example`).

Conferencing is modular under `backend/app/services/conferencing/` (mock + Microsoft Graph providers).

## Key APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/bridges` | List bridges |
| POST | `/api/bridges/incidents/{id}` | Create (+ optional invite) |
| POST | `/api/bridges/{id}/open` | Mark open / set started_at |
| POST | `/api/bridges/{id}/end` | End / set ended_at |
| POST | `/api/bridges/{id}/invite` | Invite approved responders |

## Credentials

- Demo: none  
- Optional live Teams: Microsoft Graph app registration (tenant/client/secret) + `MOCK_MODE=false`  

## Waiting for approval

Do **not** start Phase 6 (attendance / timeline) until the user approves Phase 5.
