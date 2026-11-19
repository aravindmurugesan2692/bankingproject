# OCC AI Assistant — Phase 1

Enterprise Operations Control Center platform for incident initiation and dashboard overview. **Phase 1 only**: React dashboard + FastAPI/SQLite incident create/list. Integrations and AI analysis are deferred to later phases (awaiting approval).

Banking Java app and the separate `occ-bridge/` sample are left untouched.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, Vite, Tailwind CSS v4, Lucide, React Router |
| Backend | Python FastAPI, Pydantic, SQLAlchemy, SQLite |
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
- On first start, **8 MOCK sample incidents** are seeded into SQLite.

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

### Docker (stub — Phase 1)

```bash
cd occ-ai-assistant
docker compose up --build
```

Full Docker/docs polish is planned for Phase 9.

## Phase 1 APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness + mock flag |
| GET | `/api/dashboard` | Summary cards + tables (mock-labeled) |
| GET | `/api/dashboard/summary` | Summary metrics only |
| GET | `/api/incidents` | List incidents |
| POST | `/api/incidents` | Create incident (validated) |
| GET | `/api/incidents/{id}` | Get one incident |

## Initiate Incident — mandatory fields

Required: title, description, application/service, environment (`Production` \| `QA` \| `Development`), business impact, users affected, issue start time.

Optional: error messages, affected infrastructure, additional observations.

## Credentials

**None required for Phase 1.** Later phases will use env placeholders in `.env.example` (OpenAI, ServiceNow, PagerDuty, Microsoft Graph).

## Waiting for approval

Do **not** start Phase 2 (AI analysis / team recommendations) until the user approves Phase 1.
