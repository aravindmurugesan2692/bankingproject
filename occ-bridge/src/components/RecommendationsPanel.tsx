import type { BridgeSession } from '../types'

interface Props {
  session: BridgeSession
  busy: boolean
  onApprove: () => void
}

export function RecommendationsPanel({ session, busy, onApprove }: Props) {
  const rec = session.recommendation

  if (!rec) {
    return (
      <section className="panel recommendations-panel">
        <header className="panel__header">
          <h2>AI recommendations</h2>
          <p>Recommendations appear after the incident is created.</p>
        </header>
        <p className="empty">Waiting for intake…</p>
      </section>
    )
  }

  return (
    <section className="panel recommendations-panel">
      <header className="panel__header">
        <h2>AI recommendations</h2>
        <p>Heuristic stub — review before paging a team.</p>
      </header>

      <div className="rec-summary">
        <div className="rec-team">
          <span className="muted">Recommended team</span>
          <strong>{rec.team}</strong>
        </div>
        <span className={`confidence confidence--${rec.confidence}`}>
          {rec.confidence} confidence
        </span>
      </div>

      <p className="rec-blurb">{rec.summary}</p>

      <ol className="rec-steps">
        {rec.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>

      {session.approved ? (
        <div className="approve-done">
          Engagement approved. {session.page?.team} paged via mock PagerDuty (
          {session.page?.pageId}).
        </div>
      ) : (
        <button
          type="button"
          className="approve-btn"
          disabled={busy || session.step !== 'recommendations_ready'}
          onClick={onApprove}
        >
          {busy ? 'Paging team…' : `Approve & page ${rec.team} (mock PagerDuty)`}
        </button>
      )}
    </section>
  )
}
