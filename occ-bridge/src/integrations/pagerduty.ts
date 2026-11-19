import type { PageRecord, TeamId } from '../types'

/**
 * MOCK PagerDuty integration.
 * Swap point: replace pageTeam with Events API v2 / Enqueue API
 * after management approves live credentials.
 *
 * Live path sketch (do not enable yet):
 *   POST https://events.pagerduty.com/v2/enqueue
 *   routing_key per team escalation policy
 */
const TEAM_ROUTING_KEYS: Record<TeamId, string> = {
  Linux: 'mock-rk-linux',
  Network: 'mock-rk-network',
  Database: 'mock-rk-database',
  Application: 'mock-rk-application',
}

export async function pageTeam(input: {
  team: TeamId
  incidentNumber: string
  summary: string
  requestedBy: string
}): Promise<PageRecord> {
  await delay(400)

  const pageId = `PD-${Date.now().toString(36).toUpperCase()}`

  return {
    pageId,
    team: input.team,
    status: 'triggered',
    createdAt: new Date().toISOString(),
    requestedBy: input.requestedBy,
  }
}

/** Exposed for docs / future wiring — not used by the sample UI. */
export function getMockRoutingKey(team: TeamId): string {
  return TEAM_ROUTING_KEYS[team]
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
