import type { BridgeDefinition } from '../types'

/**
 * Placeholder Teams meeting links until real STS URLs are provided.
 * Swap these values (or load from env) when live links are approved.
 */
export const BRIDGES: BridgeDefinition[] = [
  {
    id: 'STS1',
    name: 'STS1 Bridge',
    description: 'Primary critical-incident bridge',
    teamsMeetingUrl: 'https://teams.microsoft.com/l/meetup-join/sample-sts1',
  },
  {
    id: 'STS2',
    name: 'STS2 Bridge',
    description: 'Secondary critical-incident bridge',
    teamsMeetingUrl: 'https://teams.microsoft.com/l/meetup-join/sample-sts2',
  },
  {
    id: 'STS3',
    name: 'STS3 Bridge',
    description: 'Regional / overflow bridge',
    teamsMeetingUrl: 'https://teams.microsoft.com/l/meetup-join/sample-sts3',
  },
  {
    id: 'STS4',
    name: 'STS4 Bridge',
    description: 'Backup / contingency bridge',
    teamsMeetingUrl: 'https://teams.microsoft.com/l/meetup-join/sample-sts4',
  },
]

export function getBridge(id: string): BridgeDefinition | undefined {
  return BRIDGES.find((b) => b.id === id)
}
