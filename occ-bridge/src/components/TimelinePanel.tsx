import type { TimelineEvent } from '../types'

interface Props {
  events: TimelineEvent[]
  compact?: boolean
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}

export function TimelinePanel({ events, compact }: Props) {
  const ordered = [...events].reverse()

  return (
    <section className={`panel timeline-panel ${compact ? 'is-compact' : ''}`}>
      <header className="panel__header">
        <h2>Live timeline</h2>
        <p>Audit-friendly bridge activity (actor + timestamp).</p>
      </header>
      {ordered.length === 0 ? (
        <p className="empty">No events yet.</p>
      ) : (
        <ol className="timeline">
          {ordered.map((evt) => (
            <li
              key={evt.id}
              className={`timeline__item timeline__item--${evt.kind}`}
            >
              <time dateTime={evt.at}>{formatTime(evt.at)}</time>
              <span className="timeline__dot" aria-hidden />
              <div>
                <strong>{evt.label}</strong>
                <div className="timeline__meta">
                  <span className="timeline__kind">{evt.kind}</span>
                  <span className="timeline__actor">by {evt.actor}</span>
                </div>
                {evt.detail ? (
                  <p className="timeline__detail">{evt.detail}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
