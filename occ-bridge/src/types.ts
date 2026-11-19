export type BridgeId = 'STS1' | 'STS2' | 'STS3' | 'STS4'

export type Priority = 'P1' | 'P2' | 'P3' | 'P4'

export type TeamId = 'Linux' | 'Network' | 'Database' | 'Application'

export type FlowStep =
  | 'idle'
  | 'awaiting_issue'
  | 'awaiting_priority'
  | 'creating_incident'
  | 'analyzing'
  | 'recommendations_ready'
  | 'team_paged'
  | 'rejected'
  | 'closed'

export type TimelineKind =
  | 'bridge'
  | 'occ'
  | 'incident'
  | 'ai'
  | 'pagerduty'
  | 'teams'
  | 'system'
  | 'audit'

export interface TimelineEvent {
  id: string
  at: string
  label: string
  kind: TimelineKind
  /** Operator or system actor for audit trail */
  actor: string
  detail?: string
}

export interface Recommendation {
  team: TeamId
  summary: string
  steps: string[]
  confidence: 'high' | 'medium' | 'low'
}

export interface IncidentRecord {
  number: string
  sysId: string
  shortDescription: string
  priority: Priority
  bridgeId: BridgeId
  createdAt: string
  createdBy: string
}

export interface PageRecord {
  pageId: string
  team: TeamId
  status: 'triggered' | 'acknowledged'
  createdAt: string
  requestedBy: string
}

export interface BridgeSession {
  id: string
  bridgeId: BridgeId
  startedAt: string
  endedAt?: string
  step: FlowStep
  operator: string
  issue?: string
  priority?: Priority
  incident?: IncidentRecord
  recommendation?: Recommendation
  page?: PageRecord
  timeline: TimelineEvent[]
  decision?: 'approved' | 'rejected'
  rejectionReason?: string
}

export interface BridgeDefinition {
  id: BridgeId
  name: string
  description: string
  teamsMeetingUrl: string
}

export interface OccOperator {
  name: string
  signedInAt: string
}

export interface AppConfig {
  bridges: BridgeDefinition[]
  mockMode: true
}
