import type { BridgeDefinition } from '../types'

/**
 * Default placeholder Teams meeting links.
 * Editable at runtime via Config page (persisted in localStorage).
 * Replace with real STS URLs after management approval.
 */
export const DEFAULT_BRIDGES: BridgeDefinition[] = [
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

export const STORAGE = {
  auth: 'occ-bridge-auth-v2',
  active: 'occ-bridge-active-v2',
  history: 'occ-bridge-history-v2',
  config: 'occ-bridge-config-v2',
} as const
