import { useState } from 'react'
import type { BridgeSession } from '../types'

interface Props {
  session: BridgeSession
  busy: boolean
  onApprove: () => void
  onReject: (reason: string) => void
}

export function RecommendationsPanel({
  session,
  busy,
  onApprove,
  onReject,
}: Props) {
  const [reason, setReason] = useState('')
  const [showReject, setShowReject] = useState(false)
  const rec = session.recommendation

  if (!rec) {
    return (
      <section className="panel recommendations-panel">
        <header className="panel__header">
          <h2>AI recommendations</h2>
          <p>Recommendations appear after the incident is created.</p>
        </header>
        <p className="empty">
          {session.step === 'analyzing'
            ? 'Analyzing issue…'
            : 'Waiting for intake…'}
        </p>
      </section>
    )
  }

  const decided = Boolean(session.decision)

  return (
    <section className="panel recommendations-panel">
      <header className="panel__header">
        <h2>AI recommendations</h2>
        <p>Heuristic stub — OCC must Approve or Reject before paging.</p>
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

      {session.decision === 'approved' && session.page ? (
        <div className="approve-done">
          Approved by {session.operator}. {session.page.team} paged via mock
          PagerDuty ({session.page.pageId}).
        </div>
      ) : null}

      {session.decision === 'rejected' ? (
        <div className="reject-done">
          Rejected by {session.operator}. Reason:{' '}
          {session.rejectionReason ?? '—'}
        </div>
      ) : null}

      {!decided && session.step === 'recommendations_ready' ? (
        <div className="decision-actions">
          <button
            type="button"
            className="approve-btn"
            disabled={busy}
            onClick={onApprove}
          >
            {busy ? 'Paging team…' : `Approve & page ${rec.team}`}
          </button>
          <button
            type="button"
            className="ghost"
            disabled={busy}
            onClick={() => setShowReject((v) => !v)}
          >
            Reject
          </button>
        </div>
      ) : null}

      {showReject && !decided ? (
        <form
          className="reject-form"
          onSubmit={(e) => {
            e.preventDefault()
            onReject(reason)
            setShowReject(false)
          }}
        >
          <label htmlFor="reject-reason">
            Rejection reason
            <textarea
              id="reject-reason"
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Wrong team — waiting on more diagnostics"
              disabled={busy}
            />
          </label>
          <button type="submit" className="danger-btn" disabled={busy}>
            Confirm reject
          </button>
        </form>
      ) : null}
    </section>
  )
}
