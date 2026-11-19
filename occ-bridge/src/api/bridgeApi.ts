/**
 * Shared API layer used by the web console and Teams bot UI.
 * Both surfaces call these helpers so session state stays in sync.
 *
 * Today this wraps the in-browser store + mock integrations.
 * Later: point these functions at real HTTP/backends without rewriting UI.
 */
export {
  approveEngagement,
  clearHistory,
  endBridge,
  getBridgeConfig,
  getHistorySession,
  getSnapshot,
  rejectEngagement,
  resetBridgeUrls,
  signIn,
  signOut,
  startBridge,
  submitIssue,
  submitPriority,
  subscribe,
  updateBridgeUrl,
} from '../store/appStore'

export { openTeamsMeeting, getTeamsMeetingUrl, sendBotMessage } from '../integrations/teams'
