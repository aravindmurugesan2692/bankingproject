import type {
  DashboardBundle,
  Incident,
  IncidentAnalysis,
  IncidentCreatePayload,
  IncidentCreateResponse,
  SupportTeam,
} from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
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
