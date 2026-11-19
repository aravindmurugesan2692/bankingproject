import type { BridgeId } from '../types'
import { getBridgeConfig } from '../store/appStore'

/**
 * MOCK Teams / Azure Bot integration.
 * Swap point: replace helpers with Azure Bot Framework + Graph
 * after management approves bot registration and real meeting URLs.
 *
 * The in-app Teams bot UI shares the same session API as the web console.
 * Meeting links are loaded from app config (editable in Config).
 */

export function getTeamsMeetingUrl(bridgeId: BridgeId): string {
  const bridge = getBridgeConfig(bridgeId)
  return bridge?.teamsMeetingUrl ?? '#'
}

export function openTeamsMeeting(bridgeId: BridgeId): void {
  const url = getTeamsMeetingUrl(bridgeId)
  window.open(url, '_blank', 'noopener,noreferrer')
}

/**
 * Placeholder for future Azure Bot message send.
 * Currently a no-op that returns a mock message id.
 */
export async function sendBotMessage(
  bridgeId: BridgeId,
  text: string,
): Promise<{ messageId: string }> {
  void bridgeId
  void text
  await delay(200)
  return { messageId: `bot-msg-${Date.now()}` }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
