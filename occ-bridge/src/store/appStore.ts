import { analyzeIssue } from '../ai/recommend'
import { DEFAULT_BRIDGES, STORAGE } from '../config/defaults'
import { createIncident } from '../integrations/servicenow'
import { pageTeam } from '../integrations/pagerduty'
import type {
  BridgeDefinition,
  BridgeId,
  BridgeSession,
  OccOperator,
  Priority,
  TimelineEvent,
  TimelineKind,
} from '../types'

type Listener = () => void

interface AppState {
  operator: OccOperator | null
  bridges: BridgeDefinition[]
  active: BridgeSession | null
  history: BridgeSession[]
}

const listeners = new Set<Listener>()

let state: AppState = {
  operator: loadJson(STORAGE.auth, null),
  bridges: loadJson(STORAGE.config, DEFAULT_BRIDGES),
  active: loadJson(STORAGE.active, null),
  history: loadJson(STORAGE.history, []),
}

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function persistAll() {
  if (state.operator) {
    localStorage.setItem(STORAGE.auth, JSON.stringify(state.operator))
  } else {
    localStorage.removeItem(STORAGE.auth)
  }
  localStorage.setItem(STORAGE.config, JSON.stringify(state.bridges))
  if (state.active) {
    localStorage.setItem(STORAGE.active, JSON.stringify(state.active))
  } else {
    localStorage.removeItem(STORAGE.active)
  }
  localStorage.setItem(STORAGE.history, JSON.stringify(state.history))
  listeners.forEach((l) => l())
}

function setState(partial: Partial<AppState>) {
  state = { ...state, ...partial }
  persistAll()
}

function uid(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`
}

function nowIso() {
  return new Date().toISOString()
}

function event(
  label: string,
  kind: TimelineKind,
  actor: string,
  detail?: string,
): TimelineEvent {
  return {
    id: uid('evt'),
    at: nowIso(),
    label,
    kind,
    actor,
    detail,
  }
}

function requireOperator(): OccOperator {
  if (!state.operator) throw new Error('OCC sign-in required')
  return state.operator
}

function requireActive(): BridgeSession {
  if (!state.active) throw new Error('No active bridge session')
  return state.active
}

function updateActive(next: BridgeSession) {
  setState({ active: next })
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getSnapshot(): AppState {
  return state
}

export function getBridgeConfig(id: BridgeId): BridgeDefinition | undefined {
  return state.bridges.find((b) => b.id === id)
}

export function signIn(name: string): OccOperator {
  const trimmed = name.trim()
  if (!trimmed) throw new Error('Operator name is required')
  const operator: OccOperator = {
    name: trimmed,
    signedInAt: nowIso(),
  }
  setState({ operator })
  return operator
}

export function signOut() {
  setState({ operator: null })
}

export function updateBridgeUrl(bridgeId: BridgeId, teamsMeetingUrl: string) {
  const bridges = state.bridges.map((b) =>
    b.id === bridgeId ? { ...b, teamsMeetingUrl: teamsMeetingUrl.trim() } : b,
  )
  setState({ bridges })
}

export function resetBridgeUrls() {
  setState({ bridges: DEFAULT_BRIDGES.map((b) => ({ ...b })) })
}

export async function startBridge(bridgeId: BridgeId): Promise<BridgeSession> {
  const operator = requireOperator()
  if (state.active && state.active.step !== 'closed') {
    throw new Error(
      `Bridge ${state.active.bridgeId} is already active. End it before opening another.`,
    )
  }

  const session: BridgeSession = {
    id: uid('sess'),
    bridgeId,
    startedAt: nowIso(),
    step: 'awaiting_issue',
    operator: operator.name,
    timeline: [
      event(`Bridge started — ${bridgeId}`, 'bridge', 'system'),
      event(`OCC joined — ${operator.name}`, 'occ', operator.name),
    ],
  }
  setState({ active: session })
  return session
}

export async function submitIssue(issue: string): Promise<BridgeSession> {
  const operator = requireOperator()
  const active = requireActive()
  const trimmed = issue.trim()
  if (!trimmed) throw new Error('Issue description is required')

  const next: BridgeSession = {
    ...active,
    issue: trimmed,
    step: 'awaiting_priority',
    timeline: [
      ...active.timeline,
      event('Issue captured', 'audit', operator.name, trimmed),
    ],
  }
  updateActive(next)
  return next
}

export async function submitPriority(priority: Priority): Promise<BridgeSession> {
  const operator = requireOperator()
  const active = requireActive()
  if (!active.issue) throw new Error('Issue is required before priority')

  let next: BridgeSession = {
    ...active,
    priority,
    step: 'creating_incident',
    timeline: [
      ...active.timeline,
      event(`Priority set — ${priority}`, 'audit', operator.name),
    ],
  }
  updateActive(next)

  try {
    const incident = await createIncident({
      shortDescription: active.issue,
      priority,
      bridgeId: active.bridgeId,
      createdBy: operator.name,
    })

    next = {
      ...next,
      incident,
      step: 'analyzing',
      timeline: [
        ...next.timeline,
        event(
          `Incident created (${incident.number})`,
          'incident',
          operator.name,
          `sys_id=${incident.sysId}`,
        ),
      ],
    }
    updateActive(next)

    const recommendation = await analyzeIssue(active.issue)

    next = {
      ...next,
      recommendation,
      step: 'recommendations_ready',
      timeline: [
        ...next.timeline,
        event(
          `AI recommendation ready — ${recommendation.team} (${recommendation.confidence})`,
          'ai',
          'ai-stub',
          recommendation.summary,
        ),
      ],
    }
    updateActive(next)
    return next
  } catch (err) {
    next = {
      ...next,
      step: 'awaiting_priority',
      timeline: [
        ...next.timeline,
        event(
          'Incident create failed — returned to priority step',
          'system',
          'system',
          err instanceof Error ? err.message : 'Unknown error',
        ),
      ],
    }
    updateActive(next)
    throw err
  }
}

export async function approveEngagement(): Promise<BridgeSession> {
  const operator = requireOperator()
  const active = requireActive()
  if (!active.recommendation || !active.incident) {
    throw new Error('Nothing to approve yet')
  }
  if (active.decision) {
    throw new Error('A decision was already recorded for this bridge')
  }

  const page = await pageTeam({
    team: active.recommendation.team,
    incidentNumber: active.incident.number,
    summary: active.issue ?? active.recommendation.summary,
    requestedBy: operator.name,
  })

  const next: BridgeSession = {
    ...active,
    page,
    decision: 'approved',
    step: 'team_paged',
    timeline: [
      ...active.timeline,
      event(
        `Engagement approved — page ${page.team}`,
        'audit',
        operator.name,
      ),
      event(
        `${page.team} team involved (PagerDuty ${page.pageId})`,
        'pagerduty',
        operator.name,
        `status=${page.status}`,
      ),
      event(
        `${page.team} engineer joining Teams bridge…`,
        'teams',
        'system',
      ),
    ],
  }
  updateActive(next)
  return next
}

export async function rejectEngagement(reason: string): Promise<BridgeSession> {
  const operator = requireOperator()
  const active = requireActive()
  if (!active.recommendation) {
    throw new Error('Nothing to reject yet')
  }
  if (active.decision) {
    throw new Error('A decision was already recorded for this bridge')
  }

  const trimmed = reason.trim() || 'No reason provided'
  const next: BridgeSession = {
    ...active,
    decision: 'rejected',
    rejectionReason: trimmed,
    step: 'rejected',
    timeline: [
      ...active.timeline,
      event('Engagement rejected — team not paged', 'audit', operator.name, trimmed),
    ],
  }
  updateActive(next)
  return next
}

export function endBridge(): BridgeSession | null {
  const operator = state.operator
  const active = state.active
  if (!active) return null

  const closed: BridgeSession = {
    ...active,
    step: 'closed',
    endedAt: nowIso(),
    timeline: [
      ...active.timeline,
      event(
        'Bridge ended',
        'bridge',
        operator?.name ?? 'system',
      ),
    ],
  }

  setState({
    active: null,
    history: [closed, ...state.history].slice(0, 50),
  })
  return closed
}

export function getHistorySession(id: string): BridgeSession | undefined {
  if (state.active?.id === id) return state.active
  return state.history.find((s) => s.id === id)
}

export function clearHistory() {
  setState({ history: [] })
}
