import { Link, useNavigate } from 'react-router-dom'
import { clearHistory } from '../api/bridgeApi'
import { EmptyState } from '../components/EmptyState'
import { useBridgeHistory } from '../hooks/useAppStore'

function formatWhen(iso?: string) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export function HistoryPage() {
  const history = useBridgeHistory()
  const navigate = useNavigate()

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Session history</h1>
          <p className="lede">
            Past bridges with incident numbers, decisions, and audit timeline.
          </p>
        </div>
        {history.length > 0 ? (
          <button
            type="button"
            className="ghost danger"
            onClick={() => {
              if (window.confirm('Clear all local history?')) clearHistory()
            }}
          >
            Clear history
          </button>
        ) : null}
      </header>

      {history.length === 0 ? (
        <EmptyState
          title="No past bridges"
          body="When you end an active bridge, it is archived here (local only)."
          action={
            <Link className="text-link" to="/">
              Open a bridge
            </Link>
          }
        />
      ) : (
        <div className="panel">
          <ul className="history-table">
            <li className="history-table__head">
              <span>Bridge</span>
              <span>Incident</span>
              <span>Decision</span>
              <span>Operator</span>
              <span>Ended</span>
            </li>
            {history.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  className="history-table__row"
                  onClick={() => navigate(`/history/${s.id}`)}
                >
                  <span className="mono">{s.bridgeId}</span>
                  <span>{s.incident?.number ?? '—'}</span>
                  <span>{s.decision ?? s.step}</span>
                  <span>{s.operator}</span>
                  <span className="muted">{formatWhen(s.endedAt)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
