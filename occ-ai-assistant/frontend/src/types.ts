export type Environment = 'Production' | 'QA' | 'Development'

export type SeverityCode = 'P1' | 'P2' | 'P3' | 'P4'

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
  working_severity?: string | null
  working_description?: string | null
  selected_team_slugs?: string[]
  approved_by?: string | null
  approved_at?: string | null
  rejection_reason?: string | null
  servicenow_number?: string | null
  servicenow_sys_id?: string | null
  servicenow_is_mock?: boolean
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

export interface RecommendedTeam {
  team: string
  slug: string
  reason: string
}

export interface IncidentAnalysis {
  id: number
  incident_id: number
  occ_incident_id: string | null
  incident_title: string | null
  summary: string
  category: string
  suggested_priority: string
  business_impact: string
  potential_causes: string[]
  affected_application: string
  recommended_teams: RecommendedTeam[]
  troubleshooting_steps: string[]
  missing_information: string[]
  next_actions: string[]
  needs_more_info: boolean
  disclaimer: string
  provider: string
  model: string
  is_mock: boolean
  created_at: string
}

export interface IncidentCreateResponse {
  incident: Incident
  analysis: IncidentAnalysis | null
}

export interface SupportTeam {
  id: number
  name: string
  slug: string
  description: string
  ownership: string
  responsibilities: string
  pagerduty_service_id: string
  pagerduty_escalation_policy_id: string
  active: boolean
}

export interface ApprovalAuditEvent {
  id: number
  incident_id: number
  action: string
  actor: string
  detail: string
  approved_teams: string[]
  severity: string | null
  created_at: string
}

export interface PagerDutyPlaceholder {
  team: string
  slug: string
  service_id: string
  escalation_policy_id: string
}

export interface ApprovalPacket {
  incident: Incident
  analysis: IncidentAnalysis | null
  selected_teams: SupportTeam[]
  pagerduty_placeholders: PagerDutyPlaceholder[]
  servicenow_preview: Record<string, unknown>
  audit_trail: ApprovalAuditEvent[]
}

export interface ApprovalDecisionResponse {
  incident: Incident
  servicenow_number: string | null
  servicenow_sys_id: string | null
  servicenow_is_mock: boolean
  servicenow_duplicate: boolean
  pagerduty_notifications?: PagerDutyNotification[]
  audit_trail: ApprovalAuditEvent[]
}

export interface ApprovalDraftPayload {
  working_severity?: SeverityCode
  working_description?: string
  selected_team_slugs?: string[]
  actor?: string
}

export interface ApprovalDecidePayload {
  actor?: string
  rejection_reason?: string
  working_severity?: SeverityCode
  working_description?: string
  selected_team_slugs?: string[]
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
    status?: string
    pd_incident_id?: string
    mock: boolean
  }>
  pagerduty_notifications?: PagerDutyNotification[]
  mock_mode: boolean
  data_label: string
}

export interface PagerDutyNotification {
  id: number
  incident_id: number
  occ_incident_id: string
  servicenow_number: string | null
  team_slug: string
  team_name: string
  pagerduty_service_id: string
  pagerduty_escalation_policy_id: string
  pd_incident_id: string
  pd_incident_url: string
  escalation_status: string
  notified_at: string
  acknowledged_at: string | null
  is_mock: boolean
  created_at: string
}
