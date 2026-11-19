import { analyzeIssue } from '../ai/recommend'
import { createIncident } from '../integrations/servicenow'
import { pageTeam } from '../integrations/pagerduty'
import type {
  BridgeId,
  BridgeSession,
  FlowStep,
  Priority,
  TimelineEvent,
} from '../types'

const STORAGE_KEY = 'occ-bridge-session-v1'

type Listener = () => void

let session: BridgeSession | null = load()
const listeners = new Set<Listener>()

function load(): BridgeSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as BridgeSession
  } catch {
    return null
  }
}

function persist() {
  if (session) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
  listeners.forEach((l) => l())
}

function uid(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`
}

function nowIso() {
  return new Date().toISOString()
}

function pushEvent(
  label: string,
  kind: TimelineEvent['kind'],
): TimelineEvent {
  return {
    id: uid('evt'),
    at: nowIso(),
    label,
    kind,
  }
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getSession(): BridgeSession | null {
  return session
}

export function clearSession() {
  session = null
  persist()
}

export async function startBridge(bridgeId: BridgeId): Promise<BridgeSession> {
  const startedAt = nowIso()
  session = {
    id: uid('sess'),
    bridgeId,
    startedAt,
    step: 'awaiting_issue',
    approved: false,
    timeline: [
      pushEvent(`Bridge started — ${bridgeId}`, 'bridge'),
      pushEvent('OCC joined', 'occ'),
    ],
  }
  persist()
  return session
}

export async function submitIssue(issue: string): Promise<BridgeSession> {
  assertSession()
  session = {
    ...session!,
    issue: issue.trim(),
    step: 'awaiting_priority',
    timeline: [
      ...session!.timeline,
      pushEvent('Issue captured', 'system'),
    ],
  }
  persist()
  return session!
}

export async function submitPriority(priority: Priority): Promise<BridgeSession> {
  assertSession()
  const issue = session!.issue ?? ''
  const bridgeId = session!.bridgeId

  session = {
    ...session!,
    priority,
    timeline: [
      ...session!.timeline,
      pushEvent(`Priority set — ${priority}`, 'system'),
    ],
  }
  persist()

  const incident = await createIncident({
    shortDescription: issue,
    priority,
    bridgeId,
  })

  session = {
    ...session!,
    incident,
    step: 'incident_created',
    timeline: [
      ...session!.timeline,
      pushEvent(`Incident created (${incident.number})`, 'incident'),
    ],
  }
  persist()

  const recommendation = await analyzeIssue(issue)

  session = {
    ...session!,
    recommendation,
    step: 'recommendations_ready',
    timeline: [
      ...session!.timeline,
      pushEvent(
        `AI recommendation ready — ${recommendation.team} team`,
        'ai',
      ),
    ],
  }
  persist()
  return session!
}

export async function approveEngagement(): Promise<BridgeSession> {
  assertSession()
  if (!session!.recommendation || !session!.incident) {
    throw new Error('Nothing to approve yet')
  }

  const page = await pageTeam({
    team: session!.recommendation.team,
    incidentNumber: session!.incident.number,
    summary: session!.issue ?? session!.recommendation.summary,
  })

  session = {
    ...session!,
    page,
    approved: true,
    step: 'team_paged',
    timeline: [
      ...session!.timeline,
      pushEvent(
        `${page.team} team involved (PagerDuty ${page.pageId})`,
        'pagerduty',
      ),
      pushEvent(`${page.team} engineer joining bridge…`, 'teams'),
    ],
  }
  persist()
  return session!
}

export function setStep(step: FlowStep) {
  assertSession()
  session = { ...session!, step }
  persist()
}

function assertSession() {
  if (!session) throw new Error('No active bridge session')
}
