import { Link, useParams } from 'react-router-dom'
import { getHistorySession } from '../api/bridgeApi'
import { EmptyState } from '../components/EmptyState'
import { TimelinePanel } from '../components/TimelinePanel'
import { useAppStore } from '../hooks/useAppStore'

export function HistoryDetailPage() {
  const { sessionId } = useParams()
  // Re-subscribe so detail stays live if active session matches
  useAppStore()
  const session = sessionId ? getHistorySession(sessionId) : undefined

  if (!session) {
    return (
      <div className="page">
        <EmptyState
          title="Session not found"
          body="This bridge session is not in local history."
          action={
            <Link className="text-link" to="/history">
              Back to history
            </Link>
          }
        />
      </div>
    )
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Session {session.id}</p>
          <h1>
            {session.bridgeId}{' '}
            <span className="muted">
              {session.endedAt ? 'closed' : 'active'}
            </span>
          </h1>
        </div>
        <Link className="ghost link-btn" to="/history">
          Back
        </Link>
      </header>

      <div className="console-grid">
        <section className="panel">
          <header className="panel__header">
            <h2>Summary</h2>
          </header>
          <dl className="kv">
            <div>
              <dt>Operator</dt>
              <dd>{session.operator}</dd>
            </div>
            <div>
              <dt>Issue</dt>
              <dd>{session.issue ?? '—'}</dd>
            </div>
            <div>
              <dt>Priority</dt>
              <dd>{session.priority ?? '—'}</dd>
            </div>
            <div>
              <dt>Incident</dt>
              <dd>{session.incident?.number ?? '—'}</dd>
            </div>
            <div>
              <dt>Decision</dt>
              <dd>
                {session.decision ?? '—'}
                {session.rejectionReason
                  ? ` — ${session.rejectionReason}`
                  : ''}
              </dd>
            </div>
            <div>
              <dt>PagerDuty</dt>
              <dd>
                {session.page
                  ? `${session.page.team} · ${session.page.pageId}`
                  : '—'}
              </dd>
            </div>
          </dl>
        </section>
        <TimelinePanel events={session.timeline} />
      </div>
    </div>
  )
}
