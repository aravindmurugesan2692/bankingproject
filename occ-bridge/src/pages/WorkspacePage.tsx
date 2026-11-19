import { Link, useNavigate } from 'react-router-dom'
import {
  approveEngagement,
  endBridge,
  getBridgeConfig,
  openTeamsMeeting,
  rejectEngagement,
  submitIssue,
  submitPriority,
} from '../api/bridgeApi'
import { EmptyState } from '../components/EmptyState'
import { ErrorBanner } from '../components/ErrorBanner'
import { IncidentPanel } from '../components/IncidentPanel'
import { IntakePanel } from '../components/IntakePanel'
import { RecommendationsPanel } from '../components/RecommendationsPanel'
import { TimelinePanel } from '../components/TimelinePanel'
import { useActiveSession } from '../hooks/useAppStore'
import { useAsyncAction } from '../hooks/useAsyncAction'
import type { Priority } from '../types'

export function WorkspacePage() {
  const session = useActiveSession()
  const navigate = useNavigate()
  const { busy, error, run, clearError } = useAsyncAction()

  if (!session) {
    return (
      <div className="page">
        <EmptyState
          title="No active bridge"
          body="Open STS1–STS4 from Bridge home or start one in the Teams bot."
          action={
            <Link className="text-link" to="/">
              Go to bridge home
            </Link>
          }
        />
      </div>
    )
  }

  const bridge = getBridgeConfig(session.bridgeId)

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{session.bridgeId} workspace</p>
          <h1>{bridge?.name ?? session.bridgeId}</h1>
          <p className="lede">
            Issue intake, incident, AI triage, and OCC approve/reject — synced
            with the Teams bot.
          </p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="ghost"
            onClick={() => openTeamsMeeting(session.bridgeId)}
          >
            Open Teams meeting
          </button>
          <Link className="ghost link-btn" to="/bot">
            Open Teams bot
          </Link>
          <button
            type="button"
            className="ghost danger"
            disabled={busy}
            onClick={() => {
              endBridge()
              navigate('/history')
            }}
          >
            End bridge
          </button>
        </div>
      </header>

      <ErrorBanner message={error} onDismiss={clearError} />

      <div className="session-bar">
        <span className="session-bridge">{session.bridgeId}</span>
        <span className="muted">Operator {session.operator}</span>
        <span className="session-step">
          Step: {session.step.replaceAll('_', ' ')}
        </span>
      </div>

      <div className="console-grid">
        <div className="console-main">
          <IntakePanel
            session={session}
            busy={busy}
            onSubmitIssue={(issue) => run(() => submitIssue(issue))}
            onSubmitPriority={(p: Priority) => run(() => submitPriority(p))}
          />
          <IncidentPanel session={session} />
          <RecommendationsPanel
            session={session}
            busy={busy}
            onApprove={() => run(() => approveEngagement())}
            onReject={(reason) => run(() => rejectEngagement(reason))}
          />
        </div>
        <div className="console-side">
          <TimelinePanel events={session.timeline} />
        </div>
      </div>
    </div>
  )
}
