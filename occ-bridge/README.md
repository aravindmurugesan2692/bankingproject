# OCC Bridge Assist (SAMPLE)

Sample Operation Center demo for live incident bridges **STS1–STS4**.

OCC operators can open a bridge in the web console (meant to sit beside Teams), walk through issue → priority → mock ServiceNow incident → AI recommendations → OCC approve → mock PagerDuty page, and watch a live timeline update. A **simulated Teams bot chat** is included and labeled as sample until Azure Bot registration exists.

> **SAMPLE / MOCK** — No real ServiceNow, PagerDuty, or Azure Bot calls. Live APIs require management approval.

## How to run locally

```bash
cd occ-bridge
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`).

Production build check:

```bash
npm run build
npm run preview
```

## Happy path (demo)

1. Click **STS1**, **STS2**, **STS3**, or **STS4**.
2. Timeline shows `Bridge started` and `OCC joined`.
3. Enter an issue (try keywords like `linux`, `network`, `database`, or `api`).
4. Choose priority **P1–P4**.
5. Mock ServiceNow creates `INC…` → timeline updates.
6. AI stub recommends a team + fix steps.
7. Click **Approve & page …** (or Approve in the bot shell).
8. Mock PagerDuty pages the team → timeline shows team involved.
9. Optional: **Open Teams meeting (placeholder)** uses sample meeting links.

Session state is kept in `localStorage` (`occ-bridge-session-v1`) so a refresh keeps the active bridge. **End bridge** clears it.

## Surfaces

| Surface | Status |
|---------|--------|
| Web console | Implemented (OCC primary UI) |
| Teams bot chat | Simulated in-browser shell, labeled SAMPLE |
| Teams meeting links | Placeholders in `src/data/bridges.ts` |

## Mock integrations (swap points)

| Module | Role | Live swap later |
|--------|------|-----------------|
| `src/integrations/servicenow.ts` | `createIncident()` returns fake `INC…` | ServiceNow Table / Import Set API |
| `src/integrations/pagerduty.ts` | `pageTeam()` returns fake page id | Events API v2 / enqueue |
| `src/integrations/teams.ts` | Placeholder meeting URLs + no-op bot send | Azure Bot + Graph + real STS links |
| `src/ai/recommend.ts` | Keyword heuristic → Linux / Network / Database / Application | Real LLM / triage service |

Comments at the top of each integration file mark the swap points.

## Project layout

```
occ-bridge/
  src/
    ai/recommend.ts
    components/          # picker, intake, recommendations, timeline, bot shell
    data/bridges.ts      # STS1–STS4 + placeholder Teams URLs
    integrations/        # ServiceNow / PagerDuty / Teams mocks
    pages/ConsolePage.tsx
    store/sessionStore.ts
```

## Out of scope (by design)

- Real credentials / live API traffic
- Auto-paging without OCC approval
- Non-OCC / end-user intake
- More than four bridges
- Full CMDB enrichment

## Audience

OCC operators only.
