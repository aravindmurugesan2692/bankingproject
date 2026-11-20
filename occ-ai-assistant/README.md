# OCC AI Assistant — Phase 9 (final)

Enterprise OCC incident & bridge platform: initiate → AI analyze → OCC approve → ServiceNow → PagerDuty → Teams bridge → participation/timeline → AI work notes → closure/reporting → **security / Docker / docs**.

Banking app + `occ-bridge/` are untouched. All secrets come from environment variables — **never** from frontend code.

## Architecture

```
React/Vite UI  ──/api──►  FastAPI
                            ├─ SQLAlchemy / SQLite (Postgres-ready DATABASE_URL)
                            ├─ Auth-ready RBAC (OCC Engineer / Administrator / Viewer demo)
                            ├─ Audit: approval_audit_events + security_audit_events
                            └─ Integrations (MOCK by default): SN · PD · Graph · LLM
```

**RBAC (demo headers `X-OCC-User` / `X-OCC-Role`):**

| Role | Approvals / closure approve | Settings force-mock |
|------|-----------------------------|---------------------|
| OCC Engineer | Yes | No |
| OCC Administrator | Yes | Yes |
| Viewer | No (403 + audit) | No |

`AUTH_MODE=oidc` is stubbed (501) until a real IdP is wired — credentials are never invented.

## Local run

```bash
# Backend
cd occ-ai-assistant/backend
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp ../.env.example .env   # edit; keep MOCK_MODE=true for demo
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd occ-ai-assistant/frontend
npm ci
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` → `:8000`.

## Docker deploy

```bash
cd occ-ai-assistant
cp .env.example .env
docker compose up --build
```

- UI: http://localhost:8080 (nginx proxies `/api` → backend)
- API health: http://localhost:8000/api/health

## Tests

```bash
cd occ-ai-assistant/backend && python3 -m pytest -q
cd occ-ai-assistant/frontend && npm run build
```

## Credentials for live mode

Set `MOCK_MODE=false` and provide only the integrations you need (others stay mock / force-mockable in Settings):

| Integration | Env vars |
|-------------|----------|
| LLM | `OPENAI_API_KEY` (+ optional `LLM_*`) |
| ServiceNow | `SERVICENOW_INSTANCE_URL` + username/password **or** client id/secret |
| PagerDuty | `PAGERDUTY_API_KEY` |
| Teams / Graph | `MICROSOFT_TENANT_ID`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` |

Administrators can **force mock** per integration in Settings without storing secrets in the DB. Changing `MOCK_MODE` itself requires env + process restart.

## Settings page

`/settings` — demo identity (RBAC headers), integration configured/mock status, admin force-mock toggles. No secret values are ever returned by the API (`secrets_in_frontend: false`).

## Limitations

- OIDC/JWT not implemented (auth-ready demo headers only).
- Live PD resolve / some Graph attendance paths remain modular placeholders when credentials exist.
- ServiceNow standalone nav page is still a shell; SN flows live under Approvals / Reports / Closure.
- SQLite default; set `DATABASE_URL` for Postgres when ready.
