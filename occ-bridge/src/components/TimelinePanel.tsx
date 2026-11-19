import type { TimelineEvent } from '../types'

interface Props {
  events: TimelineEvent[]
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

export function TimelinePanel({ events }: Props) {
  const ordered = [...events].reverse()

  return (
    <section className="panel timeline-panel">
      <header className="panel__header">
        <h2>Live timeline</h2>
        <p>Minute-by-minute bridge activity (mock).</p>
      </header>
      {ordered.length === 0 ? (
        <p className="empty">Open a bridge to start the timeline.</p>
      ) : (
        <ol className="timeline">
          {ordered.map((evt) => (
            <li key={evt.id} className={`timeline__item timeline__item--${evt.kind}`}>
              <time dateTime={evt.at}>{formatTime(evt.at)}</time>
              <span className="timeline__dot" aria-hidden />
              <div>
                <strong>{evt.label}</strong>
                <span className="timeline__kind">{evt.kind}</span>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
