# OCC AI Assistant — Phase 6

Full runnable OCC slice through **team participation tracking + incident timeline**.

Phases: 1–5 plus **6 participation / timeline**. Banking + `occ-bridge/` untouched.

## Workflow

1. Approve → ServiceNow → PagerDuty → Teams bridge  
2. **Team Participation** — matrix of PD notify / PD ack / Teams join / attendance confirmed  
3. Sync MOCK sample attendance (labeled; offsets from real `bridge.started_at`) or record manual joins with required `joined_at`  
4. **Incident Timeline** — unified events with verification; editable manual entries + audit  

**No AI transcript / work notes** (Phase 7). Timestamps are never fabricated.

## Quick start

```bash
cd occ-ai-assistant/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd occ-ai-assistant/frontend
npm install && npm run dev
```

### Tests

```bash
cd occ-ai-assistant/backend && python3 -m pytest -q
```

## Participation rules

| Signal | Meaning |
|--------|---------|
| `pd_notify` | Team was paged |
| `pd_ack` | Page acknowledged |
| `teams_join` | Person joined the bridge |
| `attendance_confirmed` | OCC confirmed attendance |

MOCK sample attendance requires the bridge to be **opened** first so join times offset from `started_at`.

## Waiting for approval

Do **not** start Phase 7 until the user approves Phase 6.
