# OCC AI Assistant — Phase 7

Full runnable OCC slice through **AI Bridge Assistant + ServiceNow work notes**.

Phases 1–6 plus **7 reports / work notes**. Banking + `occ-bridge/` untouched.

## Workflow

1. OCC adds approved bridge transcript excerpts / manual notes (no invented activities)  
2. **Generate AI bridge update** — structured summary/hypotheses from approved sources only  
3. Root cause marked **unconfirmed** with clear disclaimer  
4. **Preview** ServiceNow work note → OCC **approve** → **post** (MOCK by default; deduped)  

No closure automation (Phase 8).

## Quick start

```bash
cd occ-ai-assistant/backend && python3 -m pytest -q
cd occ-ai-assistant/frontend && npm run build && npm run dev
```

## Waiting for approval

Do **not** start Phase 8 until the user approves Phase 7.
