export type BridgeId = 'STS1' | 'STS2' | 'STS3' | 'STS4'

export type Priority = 'P1' | 'P2' | 'P3' | 'P4'

export type TeamId = 'Linux' | 'Network' | 'Database' | 'Application'

export type FlowStep =
  | 'idle'
  | 'awaiting_issue'
  | 'awaiting_priority'
  | 'incident_created'
  | 'recommendations_ready'
  | 'team_paged'
  | 'closed'

export interface TimelineEvent {
  id: string
  at: string
  label: string
  kind:
    | 'bridge'
    | 'occ'
    | 'incident'
    | 'ai'
    | 'pagerduty'
    | 'teams'
    | 'system'
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
  createdAt: string
}

export interface PageRecord {
  pageId: string
  team: TeamId
  status: 'triggered' | 'acknowledged'
  createdAt: string
}

export interface BridgeSession {
  id: string
  bridgeId: BridgeId
  startedAt: string
  step: FlowStep
  issue?: string
  priority?: Priority
  incident?: IncidentRecord
  recommendation?: Recommendation
  page?: PageRecord
  timeline: TimelineEvent[]
  approved: boolean
}

export interface BridgeDefinition {
  id: BridgeId
  name: string
  description: string
  teamsMeetingUrl: string
}
