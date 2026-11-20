import type {
  ApprovalDecidePayload,
  ApprovalDecisionResponse,
  ApprovalDraftPayload,
  ApprovalPacket,
  DashboardBundle,
  Incident,
  IncidentAnalysis,
  IncidentCreatePayload,
  IncidentCreateResponse,
  BridgeAIUpdate,
  BridgeAttendance,
  BridgeNote,
  PagerDutyNotification,
  ParticipationRow,
  SupportTeam,
  TeamsBridge,
  TimelineEvent,
  TimelineEventAudit,
  WorkNoteDraft,
  IncidentClosure,
  ManagementDetail,
  ManagementHistoryResponse,
  ReportingMetrics,
  SettingsStatus,
} from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

/** Demo identity headers — set by AuthProvider; never carries API secrets. */
let authHeaders: Record<string, string> = {
  'X-OCC-User': 'OCC Engineer · Demo User',
  'X-OCC-Role': 'occ_engineer',
}

export function setApiAuthHeaders(headers: Record<string, string>) {
  authHeaders = { ...headers }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') {
        detail = body.detail
      } else if (Array.isArray(body?.detail)) {
        detail = body.detail
          .map((item: { loc?: string[]; msg?: string }) => {
            const field = item.loc?.slice(-1)[0] ?? 'field'
            return `${field}: ${item.msg ?? 'invalid'}`
          })
          .join('; ')
      }
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

export function fetchDashboard(): Promise<DashboardBundle> {
  return request<DashboardBundle>('/dashboard')
}

export function createIncident(payload: IncidentCreatePayload): Promise<IncidentCreateResponse> {
  return request<IncidentCreateResponse>('/incidents', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listIncidents(): Promise<Incident[]> {
  return request<Incident[]>('/incidents')
}

export function listAnalyses(): Promise<IncidentAnalysis[]> {
  return request<IncidentAnalysis[]>('/analyses')
}

export function getIncidentAnalysis(incidentId: number): Promise<IncidentAnalysis> {
  return request<IncidentAnalysis>(`/incidents/${incidentId}/analysis`)
}

export function rerunAnalysis(incidentId: number): Promise<IncidentAnalysis> {
  return request<IncidentAnalysis>(`/incidents/${incidentId}/analysis`, {
    method: 'POST',
  })
}

export function listTeams(): Promise<SupportTeam[]> {
  return request<SupportTeam[]>('/teams')
}

export function listApprovals(): Promise<ApprovalPacket[]> {
  return request<ApprovalPacket[]>('/approvals')
}

export function getApproval(incidentId: number): Promise<ApprovalPacket> {
  return request<ApprovalPacket>(`/approvals/${incidentId}`)
}

export function updateApprovalDraft(
  incidentId: number,
  payload: ApprovalDraftPayload,
): Promise<ApprovalPacket> {
  return request<ApprovalPacket>(`/approvals/${incidentId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function approveIncident(
  incidentId: number,
  payload: ApprovalDecidePayload,
): Promise<ApprovalDecisionResponse> {
  return request<ApprovalDecisionResponse>(`/approvals/${incidentId}/approve`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function rejectIncident(
  incidentId: number,
  payload: ApprovalDecidePayload,
): Promise<ApprovalDecisionResponse> {
  return request<ApprovalDecisionResponse>(`/approvals/${incidentId}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listPagerDutyNotifications(): Promise<PagerDutyNotification[]> {
  return request<PagerDutyNotification[]>('/pagerduty/notifications')
}

export function acknowledgePagerDuty(
  notificationId: number,
): Promise<PagerDutyNotification> {
  return request<PagerDutyNotification>(
    `/pagerduty/notifications/${notificationId}/acknowledge`,
    { method: 'POST' },
  )
}

export function listBridges(): Promise<TeamsBridge[]> {
  return request<TeamsBridge[]>('/bridges')
}

export function createBridge(
  incidentId: number,
  payload: { actor?: string; bridge_code?: string; invite?: boolean } = {},
): Promise<TeamsBridge> {
  return request<TeamsBridge>(`/bridges/incidents/${incidentId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function openBridge(
  bridgeId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<TeamsBridge> {
  return request<TeamsBridge>(`/bridges/${bridgeId}/open`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function endBridge(
  bridgeId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<TeamsBridge> {
  return request<TeamsBridge>(`/bridges/${bridgeId}/end`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function inviteBridge(
  bridgeId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<TeamsBridge> {
  return request<TeamsBridge>(`/bridges/${bridgeId}/invite`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function listParticipation(incidentId: number): Promise<ParticipationRow[]> {
  return request<ParticipationRow[]>(`/incidents/${incidentId}/participation`)
}

export function listAttendance(incidentId: number): Promise<BridgeAttendance[]> {
  return request<BridgeAttendance[]>(`/incidents/${incidentId}/attendance`)
}

export function syncBridgeAttendance(
  bridgeId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<BridgeAttendance[]> {
  return request<BridgeAttendance[]>(`/bridges/${bridgeId}/attendance/sync`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function confirmAttendance(
  attendanceId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<BridgeAttendance> {
  return request<BridgeAttendance>(`/attendance/${attendanceId}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function listTimeline(incidentId: number): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/timeline/incidents/${incidentId}`)
}

export function createTimelineEvent(
  incidentId: number,
  payload: {
    occurred_at: string
    detail: string
    actor?: string
    team_slug?: string
    team_name?: string
  },
): Promise<TimelineEvent> {
  return request<TimelineEvent>(`/timeline/incidents/${incidentId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function editTimelineEvent(
  eventId: number,
  payload: {
    actor?: string
    detail?: string
    occurred_at?: string
    verification_status?: string
  },
): Promise<TimelineEvent> {
  return request<TimelineEvent>(`/timeline/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function listTimelineAudits(eventId: number): Promise<TimelineEventAudit[]> {
  return request<TimelineEventAudit[]>(`/timeline/events/${eventId}/audits`)
}

export function listBridgeNotes(incidentId: number): Promise<BridgeNote[]> {
  return request<BridgeNote[]>(`/incidents/${incidentId}/bridge-notes`)
}

export function createBridgeNote(
  incidentId: number,
  payload: {
    content: string
    title?: string
    note_type?: string
    occurred_at?: string
    approve_now?: boolean
    actor?: string
  },
): Promise<BridgeNote> {
  return request<BridgeNote>(`/incidents/${incidentId}/bridge-notes`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function approveBridgeNote(
  noteId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<BridgeNote> {
  return request<BridgeNote>(`/bridge-notes/${noteId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function listBridgeUpdates(incidentId: number): Promise<BridgeAIUpdate[]> {
  return request<BridgeAIUpdate[]>(`/incidents/${incidentId}/bridge-updates`)
}

export function generateBridgeUpdate(
  incidentId: number,
  payload: { note_ids?: number[]; actor?: string } = {},
): Promise<BridgeAIUpdate> {
  return request<BridgeAIUpdate>(`/incidents/${incidentId}/bridge-updates/generate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listWorkNotes(incidentId: number): Promise<WorkNoteDraft[]> {
  return request<WorkNoteDraft[]>(`/incidents/${incidentId}/work-notes`)
}

export function previewWorkNote(
  updateId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<WorkNoteDraft> {
  return request<WorkNoteDraft>(`/bridge-updates/${updateId}/work-notes/preview`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function approveWorkNote(
  draftId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<WorkNoteDraft> {
  return request<WorkNoteDraft>(`/work-notes/${draftId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function postWorkNote(
  draftId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<{ draft: WorkNoteDraft; duplicate: boolean; is_mock: boolean }> {
  return request(`/work-notes/${draftId}/post`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function searchManagementHistory(params: {
  q?: string
  status?: string
  environment?: string
  severity?: string
  application?: string
  is_mock?: boolean
  limit?: number
  offset?: number
}): Promise<ManagementHistoryResponse> {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === '') return
    qs.set(k, String(v))
  })
  const suffix = qs.toString() ? `?${qs}` : ''
  return request<ManagementHistoryResponse>(`/management/history${suffix}`)
}

export function getManagementDetail(incidentId: number): Promise<ManagementDetail> {
  return request<ManagementDetail>(`/management/incidents/${incidentId}`)
}

export function fetchReportingMetrics(): Promise<ReportingMetrics> {
  return request<ReportingMetrics>('/management/metrics')
}

export function openClosure(
  incidentId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<IncidentClosure> {
  return request<IncidentClosure>(`/management/incidents/${incidentId}/closure`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function getClosure(
  incidentId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<IncidentClosure> {
  return request<IncidentClosure>(
    `/management/incidents/${incidentId}/closure?actor=${encodeURIComponent(actor)}`,
  )
}

export function updateClosure(
  closureId: number,
  payload: {
    restored_at?: string | null
    final_summary?: string
    timeline_summary?: string
    team_notes?: string
    remediation_notes?: string
    rca_status?: 'unconfirmed' | 'confirmed'
    rca_statement?: string
    refresh_timeline?: boolean
    actor?: string
  },
): Promise<IncidentClosure> {
  return request<IncidentClosure>(`/management/closures/${closureId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function submitClosure(
  closureId: number,
  actor = 'OCC Engineer · Demo User',
): Promise<IncidentClosure> {
  return request<IncidentClosure>(`/management/closures/${closureId}/submit`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  })
}

export function approveClosure(
  closureId: number,
  actor = 'OCC Engineer · Demo User',
  closeFully = true,
): Promise<IncidentClosure> {
  return request<IncidentClosure>(`/management/closures/${closureId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ actor, close_fully: closeFully }),
  })
}

export function rejectClosure(
  closureId: number,
  reason: string,
  actor = 'OCC Engineer · Demo User',
): Promise<IncidentClosure> {
  return request<IncidentClosure>(`/management/closures/${closureId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ actor, reason }),
  })
}

export function fetchSettings(): Promise<SettingsStatus> {
  return request<SettingsStatus>('/settings')
}

export function fetchWhoAmI(): Promise<{
  user_id: string
  display_name: string
  role: string
  permissions: string[]
}> {
  return request('/settings/me')
}

export function updateForceMocks(payload: {
  force_mock_llm?: boolean
  force_mock_servicenow?: boolean
  force_mock_pagerduty?: boolean
  force_mock_teams?: boolean
  actor?: string
}): Promise<SettingsStatus> {
  return request<SettingsStatus>('/settings/force-mocks', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function recordDemoIdentity(payload: {
  display_name: string
  role: string
}): Promise<{
  ok: boolean
  display_name: string
  role: string
  headers: Record<string, string>
  note: string
}> {
  return request('/settings/demo-identity', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
