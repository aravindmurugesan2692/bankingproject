import { useState } from 'react'
import { BridgePicker } from '../components/BridgePicker'
import { IntakePanel } from '../components/IntakePanel'
import { RecommendationsPanel } from '../components/RecommendationsPanel'
import { SampleBanner } from '../components/SampleBanner'
import { TeamsBotShell } from '../components/TeamsBotShell'
import { TimelinePanel } from '../components/TimelinePanel'
import { getBridge } from '../data/bridges'
import { useSession } from '../hooks/useSession'
import { openTeamsMeeting } from '../integrations/teams'
import {
  approveEngagement,
  clearSession,
  startBridge,
  submitIssue,
  submitPriority,
} from '../store/sessionStore'
import type { BridgeId, Priority } from '../types'

export function ConsolePage() {
  const session = useSession()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(action: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setBusy(false)
    }
  }

  const bridge = session ? getBridge(session.bridgeId) : undefined

  return (
    <div className="app-shell">
      <SampleBanner />

      <header className="app-header">
        <div>
          <p className="eyebrow">Operation Center</p>
          <h1>OCC Bridge Assist</h1>
          <p className="lede">
            Open a bridge, capture the issue, create a mock incident, review AI
            triage, and page a team — all sample integrations.
          </p>
        </div>
        {session && (
          <div className="header-actions">
            <button
              type="button"
              className="ghost"
              onClick={() => openTeamsMeeting(session.bridgeId)}
            >
              Open Teams meeting (placeholder)
            </button>
            <button
              type="button"
              className="ghost danger"
              disabled={busy}
              onClick={() => clearSession()}
            >
              End bridge
            </button>
          </div>
        )}
      </header>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      {!session ? (
        <BridgePicker
          disabled={busy}
          onSelect={(id: BridgeId) => run(() => startBridge(id))}
        />
      ) : (
        <>
          <div className="session-bar">
            <span className="session-bridge">{session.bridgeId}</span>
            <span className="muted">{bridge?.name}</span>
            <span className="session-step">Step: {labelStep(session.step)}</span>
          </div>

          <div className="console-grid">
            <div className="console-main">
              <IntakePanel
                session={session}
                busy={busy}
                onSubmitIssue={(issue) => run(() => submitIssue(issue))}
                onSubmitPriority={(p: Priority) =>
                  run(() => submitPriority(p))
                }
              />
              <RecommendationsPanel
                session={session}
                busy={busy}
                onApprove={() => run(() => approveEngagement())}
              />
            </div>
            <div className="console-side">
              <TimelinePanel events={session.timeline} />
              <TeamsBotShell
                session={session}
                busy={busy}
                onSubmitIssue={(issue) => run(() => submitIssue(issue))}
                onSubmitPriority={(p: Priority) =>
                  run(() => submitPriority(p))
                }
                onApprove={() => run(() => approveEngagement())}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function labelStep(step: string) {
  switch (step) {
    case 'awaiting_issue':
      return 'Ask issue'
    case 'awaiting_priority':
      return 'Ask priority'
    case 'incident_created':
      return 'Incident created'
    case 'recommendations_ready':
      return 'Awaiting OCC approve'
    case 'team_paged':
      return 'Team paged'
    default:
      return step
  }
}
