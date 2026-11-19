import { useNavigate } from 'react-router-dom'
import { startBridge } from '../api/bridgeApi'
import { BridgePicker } from '../components/BridgePicker'
import { EmptyState } from '../components/EmptyState'
import { ErrorBanner } from '../components/ErrorBanner'
import { useActiveSession, useBridgeHistory } from '../hooks/useAppStore'
import { useAsyncAction } from '../hooks/useAsyncAction'
import type { BridgeId } from '../types'

export function HomePage() {
  const navigate = useNavigate()
  const active = useActiveSession()
  const history = useBridgeHistory()
  const { busy, error, run, clearError } = useAsyncAction()

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Bridge home</h1>
          <p className="lede">
            Select a bridge to open the OCC workspace. Active session and past
            bridges stay synced with the Teams bot.
          </p>
        </div>
      </header>

      <ErrorBanner message={error} onDismiss={clearError} />

      {active ? (
        <div className="callout">
          <div>
            <strong>{active.bridgeId}</strong> is active —{' '}
            <span className="muted">{active.step.replaceAll('_', ' ')}</span>
          </div>
          <button
            type="button"
            className="ghost"
            onClick={() => navigate('/workspace')}
          >
            Open workspace
          </button>
        </div>
      ) : null}

      <BridgePicker
        disabled={busy}
        activeBridgeId={active?.bridgeId}
        onSelect={(id: BridgeId) => {
          if (active) {
            navigate('/workspace')
            return
          }
          void run(async () => {
            await startBridge(id)
            navigate('/workspace')
          })
        }}
      />

      <section className="panel recent-panel">
        <header className="panel__header">
          <h2>Recent bridges</h2>
          <p>Quick view of closed sessions.</p>
        </header>
        {history.length === 0 ? (
          <EmptyState
            title="No history yet"
            body="Ended bridges appear here with incident and decision summary."
          />
        ) : (
          <ul className="history-list">
            {history.slice(0, 5).map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  className="history-row"
                  onClick={() => navigate(`/history/${s.id}`)}
                >
                  <span className="mono">{s.bridgeId}</span>
                  <span>{s.incident?.number ?? 'No INC'}</span>
                  <span className="muted">
                    {s.decision ?? s.step} · {s.operator}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
