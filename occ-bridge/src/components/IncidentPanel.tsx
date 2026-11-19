import type { BridgeSession } from '../types'

interface Props {
  session: BridgeSession
}

export function IncidentPanel({ session }: Props) {
  const incident = session.incident

  return (
    <section className="panel incident-panel">
      <header className="panel__header">
        <h2>ServiceNow incident</h2>
        <p>Mock ticket created from issue + priority.</p>
      </header>
      {!incident ? (
        <p className="empty">No incident yet — complete intake first.</p>
      ) : (
        <dl className="kv">
          <div>
            <dt>Number</dt>
            <dd className="mono">{incident.number}</dd>
          </div>
          <div>
            <dt>Priority</dt>
            <dd>{incident.priority}</dd>
          </div>
          <div>
            <dt>Bridge</dt>
            <dd>{incident.bridgeId}</dd>
          </div>
          <div>
            <dt>Created by</dt>
            <dd>{incident.createdBy}</dd>
          </div>
          <div>
            <dt>Short description</dt>
            <dd>{incident.shortDescription}</dd>
          </div>
          <div>
            <dt>sys_id</dt>
            <dd className="mono muted">{incident.sysId}</dd>
          </div>
        </dl>
      )}
    </section>
  )
}
