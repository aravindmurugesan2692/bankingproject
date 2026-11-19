# OCC AI Assistant — Phase 2 (full product slice)

Complete, runnable OCC workflow for **incident initiation → AI analysis → support-team recommendations**.

Banking Java app and `occ-bridge/` are untouched — only `occ-ai-assistant/` is extended.

## What you can run today

1. **Dashboard** — live summary cards + tables (MOCK-labeled seed data)
2. **Initiate Incident** — validated form → `POST /api/incidents` → SQLite persist
3. **Auto AI analysis** — structured JSON hypotheses (LLM or heuristic MOCK fallback)
4. **Incident Analysis** — full review UI (priority, causes, teams, missing info, disclaimer)
5. **Support Team Configuration** — 10-team catalog with ownership + PagerDuty placeholders

Approvals / ServiceNow are **Phase 3** (not in this slice).

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
- First start seeds **8 MOCK incidents**, **MOCK analyses**, and **10 support teams**.

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

## End-to-end demo path

1. Open Dashboard — confirm MOCK cards and seeded incidents  
2. Click an incident ID → Incident Analysis (seeded MOCK analysis)  
3. Or **Initiate Incident** → fill mandatory fields → Create  
4. App navigates to Analysis with P1–P4, recommended teams, troubleshooting, disclaimer  
5. Open **Support Team Configuration** to inspect ownership / PD placeholders  

## LLM mode

| Condition | Behaviour |
|-----------|-----------|
| `MOCK_MODE=true` (default) or empty `OPENAI_API_KEY` | Heuristic MOCK analysis |
| `MOCK_MODE=false` + `OPENAI_API_KEY` set | Live OpenAI-compatible chat completions |
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

Application Support, Linux Administration, Windows Administration, Infrastructure, Network, Database, Kubernetes / Container Platform, Storage, Security, Cloud Operations.

**No employee names.** PagerDuty IDs are placeholders until Phase 4.

## Credentials

- **Demo:** none (`MOCK_MODE=true`)
- **Optional live LLM:** `OPENAI_API_KEY` (+ `MOCK_MODE=false`, `LLM_MODEL`, `LLM_BASE_URL`)

## Waiting for approval

Phase 3 (OCC approval + ServiceNow) follows separately after this Phase 2 PR.
