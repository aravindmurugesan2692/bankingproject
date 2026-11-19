export type Environment = 'Production' | 'QA' | 'Development'

export interface Incident {
  id: number
  occ_incident_id: string
  title: string
  description: string
  application_service: string
  environment: string
  business_impact: string
  users_affected: number
  issue_start_time: string
  error_messages: string | null
  affected_infrastructure: string | null
  additional_observations: string | null
  status: string
  priority: string
  is_mock: boolean
  ack_minutes: number | null
  resolution_minutes: number | null
  bridge_active: boolean
  created_at: string
  updated_at: string
  created_by: string
}

export interface IncidentCreatePayload {
  title: string
  description: string
  application_service: string
  environment: Environment
  business_impact: string
  users_affected: number
  issue_start_time: string
  error_messages?: string | null
  affected_infrastructure?: string | null
  additional_observations?: string | null
  created_by?: string
}

export interface DashboardSummary {
  total_incidents: number
  active_incidents: number
  critical_incidents: number
  pending_approvals: number
  active_bridges: number
  resolved_incidents: number
  avg_ack_minutes: number | null
  avg_resolution_minutes: number | null
  mock_mode: boolean
  data_label: string
}

export interface DashboardBundle {
  summary: DashboardSummary
  active_incidents: Incident[]
  recent_incidents: Incident[]
  priority_distribution: Record<string, number>
  recent_activities: Array<{
    time: string
    actor: string
    detail: string
    mock: boolean
  }>
  active_bridges: Array<{
    bridge: string
    incident_id: string
    title: string
    participants: number
    status: string
    mock: boolean
  }>
  pending_acknowledgements: Array<{
    team: string
    incident_id: string
    wait_minutes: number
    mock: boolean
  }>
  mock_mode: boolean
  data_label: string
}
