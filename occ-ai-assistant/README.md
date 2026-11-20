# OCC AI Assistant — Phase 8

Full runnable OCC slice through **incident closure automation + history/reporting**.

Phases 1–7 plus **8 management / closure**. Banking + `occ-bridge/` untouched.

## Workflow

1. After service recovery, OCC opens a **closure draft** (Active incidents only)  
2. Capture **restore time** (OCC-provided — never fabricated), final summary, timeline, team/remediation notes, RCA unconfirmed vs confirmed  
3. **Submit** for OCC approval — SN resolve / PD sync stay blocked  
4. OCC **approve** → resolve ServiceNow + sync PagerDuty (MOCK by default) → mark Closed  
5. **Incident Management** page: search/filters/detail + reporting metrics from real app data (seeded rows labeled **MOCK**)

Never close an incident solely based on AI.

## Quick start

```bash
cd occ-ai-assistant/backend && python3 -m pytest -q
# terminal 1
cd occ-ai-assistant/backend && uvicorn app.main:app --reload --port 8000
# terminal 2
cd occ-ai-assistant/frontend && npm run build && npm run dev
```

Open http://localhost:5173/management

## Waiting for approval

Do **not** start Phase 9 until the user approves Phase 8.
