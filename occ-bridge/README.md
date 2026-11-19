# OCC Bridge Assist

Full Operation Center application for live incident bridges **STS1–STS4**.

OCC operators sign in, open a bridge in the web console (meant to sit beside Teams), and/or drive the same flow from the in-app **Teams bot**. Issue → priority → mock ServiceNow incident → AI recommendations → **Approve or Reject** → mock PagerDuty page → audit timeline. Session history and Teams link config are included.

> **SAMPLE / MOCK integrations** — No real ServiceNow, PagerDuty, or Azure Bot calls yet. Live APIs require management approval. The product UI and flow are complete; adapters are mocked.

## How to run

```bash
cd occ-bridge
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`).

```bash
npm run build
npm run preview
```

## Operator walkthrough

1. Sign in with an OCC operator name (local auth gate).
2. On **Bridges**, open STS1–STS4 (or start from **Teams bot**).
3. In **Workspace**: enter issue → set priority → mock INC created → AI recommends a team.
4. **Approve** (PagerDuty mock page) or **Reject** (reason logged, no page).
5. Watch the **timeline** (actor + timestamp + detail).
6. Optional: open placeholder Teams meeting; edit links under **Config**.
7. **End bridge** → archived under **History**.

Console and bot share one active session via `src/api/bridgeApi.ts`.

## Architecture

```
occ-bridge/src/
  api/bridgeApi.ts          Shared façade (console + bot)
  store/appStore.ts         Auth, config, active session, history (localStorage)
  integrations/             Mock adapters (swap for live APIs)
    servicenow.ts
    pagerduty.ts
    teams.ts
  ai/recommend.ts           Keyword triage stub
  pages/                    login, home, workspace, bot, history, config
  components/               intake, incident, recommendations, timeline, TeamsBot
  config/defaults.ts        Default STS Teams placeholders
  types.ts                  Typed domain models
```

### Routing

| Path | Purpose |
|------|---------|
| `/login` | OCC operator sign-in |
| `/` | Bridge home STS1–4 + recent history |
| `/workspace` | Active bridge workspace |
| `/bot` | Full Teams bot experience |
| `/history` | Past bridge sessions |
| `/history/:id` | Session detail + timeline |
| `/config` | Placeholder Teams URLs + swap-point docs |

### Persistence (local)

- `occ-bridge-auth-v2` — signed-in operator
- `occ-bridge-active-v2` — active bridge session
- `occ-bridge-history-v2` — closed sessions (max 50)
- `occ-bridge-config-v2` — Teams meeting URLs

## Mock vs live

| Module | Today | Later |
|--------|-------|-------|
| `integrations/servicenow.ts` | Fake `INC…` | Table / Import Set API |
| `integrations/pagerduty.ts` | Fake page id | Events API v2 |
| `integrations/teams.ts` | Placeholder links + in-app bot UI | Azure Bot + Graph + real STS URLs |
| `ai/recommend.ts` | Keyword heuristics | Real LLM / triage |

## Audience

OCC operators only.

## Out of scope until asked

- Live credentials / production traffic
- Auto-paging without OCC approval
- Non-OCC intake UI
- More than four bridges
- Full CMDB enrichment
