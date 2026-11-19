# OCC AI Assistant — Phase 2

Enterprise Operations Control Center platform. **Phases 1–2 complete**: dashboard, incident initiation, configurable LLM / heuristic analysis, and support-team recommendations.

Banking Java app and `occ-bridge/` are left untouched — only `occ-ai-assistant/` is extended.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, Vite, Tailwind CSS v4, Lucide, React Router |
| Backend | Python FastAPI, Pydantic, SQLAlchemy, SQLite |
| AI | OpenAI-compatible LLM via env, or heuristic MOCK fallback |
| Config | `.env` / `.env.example` — `MOCK_MODE=true` by default |

## Quick start

### 1. Backend

```bash
cd occ-ai-assistant/backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env     # optional; defaults work for local mock
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/api/health  
- First start seeds **8 MOCK incidents** + **10 support teams**.

### 2. Frontend

```bash
cd occ-ai-assistant/frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` → `http://127.0.0.1:8000`.

### 3. Tests (backend)

```bash
cd occ-ai-assistant/backend
source .venv/bin/activate
pytest -q
```

### Docker (stub)

```bash
cd occ-ai-assistant
docker compose up --build
```

Full Docker polish is Phase 9.

## Phase 2 behaviour

1. OCC submits **Initiate Incident**.
2. Backend persists the incident and **auto-runs analysis**.
3. UI navigates to **Incident Analysis** with structured JSON fields:
   summary, category, suggested P1–P4, business impact, potential causes,
   affected app, recommended teams + reasons, troubleshooting steps,
   missing information, next actions.
4. Analysis is labeled **hypothesis / not confirmed root cause**.
5. If information is thin, `needs_more_info` is set and missing fields are listed.

### LLM mode

| Condition | Behaviour |
|-----------|-----------|
| `MOCK_MODE=true` (default) or empty `OPENAI_API_KEY` | Heuristic MOCK analysis |
| `MOCK_MODE=false` + `OPENAI_API_KEY` set | Live OpenAI-compatible chat completions (`LLM_BASE_URL` / `LLM_MODEL`) |
| Live call fails | Automatic heuristic fallback |

## APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness + mock / LLM flags |
| GET | `/api/dashboard` | Summary cards + tables |
| GET | `/api/incidents` | List incidents |
| POST | `/api/incidents` | Create incident **and** run analysis |
| GET | `/api/incidents/{id}` | Get one incident |
| GET | `/api/incidents/{id}/analysis` | Latest analysis |
| POST | `/api/incidents/{id}/analysis` | Re-run analysis |
| GET | `/api/analyses` | Recent analyses |
| GET | `/api/teams` | Support team catalog |

## Support teams (seeded)

Application Support, Linux Administration, Windows Administration, Infrastructure, Network, Database, Kubernetes / Container Platform, Storage, Security, Cloud Operations — each with description, ownership, responsibilities, PagerDuty service/escalation placeholders, active flag. **No employee names.**

## Credentials

- **Phase 1–2 demo:** none required (`MOCK_MODE=true`).
- **Optional live LLM:** `OPENAI_API_KEY` (+ optional `LLM_MODEL`, `LLM_BASE_URL`).
- ServiceNow / PagerDuty / Microsoft Graph still unused until later phases.

## Waiting for approval

Do **not** start Phase 3 (OCC approval + ServiceNow) until the user approves Phase 2.
