import type { IncidentRecord, Priority } from '../types'

/**
 * MOCK ServiceNow integration.
 * Swap point: replace createIncident with real Table API / Import Set call
 * after management approves live credentials.
 *
 * Live path sketch (do not enable yet):
 *   POST {instance}/api/now/table/incident
 *   Authorization: Basic/OAuth
 */
export async function createIncident(input: {
  shortDescription: string
  priority: Priority
  bridgeId: string
}): Promise<IncidentRecord> {
  await delay(450)

  const seq = Math.floor(1000000 + Math.random() * 8999999)
  const number = `INC${seq}`

  return {
    number,
    sysId: `mock-sys-${seq}`,
    shortDescription: `[${input.bridgeId}] ${input.shortDescription}`,
    priority: input.priority,
    createdAt: new Date().toISOString(),
  }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
