import { useState } from 'react'
import type { BridgeSession, Priority } from '../types'

const PRIORITIES: Priority[] = ['P1', 'P2', 'P3', 'P4']

interface Props {
  session: BridgeSession
  busy: boolean
  onSubmitIssue: (issue: string) => void
  onSubmitPriority: (priority: Priority) => void
}

export function IntakePanel({
  session,
  busy,
  onSubmitIssue,
  onSubmitPriority,
}: Props) {
  const [issue, setIssue] = useState('')
  const [priority, setPriority] = useState<Priority>('P2')

  if (session.step === 'awaiting_issue') {
    return (
      <section className="panel intake-panel">
        <header className="panel__header">
          <h2>Issue intake</h2>
          <p>What is happening on this bridge?</p>
        </header>
        <form
          className="intake-form"
          onSubmit={(e) => {
            e.preventDefault()
            if (!issue.trim() || busy) return
            onSubmitIssue(issue.trim())
          }}
        >
          <label htmlFor="issue">
            Issue description
            <textarea
              id="issue"
              rows={4}
              placeholder="e.g. Linux hosts in DC1 showing high CPU and SSH timeouts"
              value={issue}
              onChange={(e) => setIssue(e.target.value)}
              disabled={busy}
            />
          </label>
          <button type="submit" disabled={busy || !issue.trim()}>
            Continue
          </button>
        </form>
      </section>
    )
  }

  if (
    session.step === 'awaiting_priority' ||
    session.step === 'creating_incident' ||
    session.step === 'analyzing'
  ) {
    return (
      <section className="panel intake-panel">
        <header className="panel__header">
          <h2>Set priority</h2>
          <p>Confirm priority before creating the ServiceNow incident.</p>
        </header>
        <div className="issue-preview">
          <span className="muted">Issue</span>
          <p>{session.issue}</p>
        </div>
        <form
          className="intake-form"
          onSubmit={(e) => {
            e.preventDefault()
            if (busy || session.step !== 'awaiting_priority') return
            onSubmitPriority(priority)
          }}
        >
          <fieldset
            className="priority-set"
            disabled={busy || session.step !== 'awaiting_priority'}
          >
            <legend>Priority</legend>
            <div className="priority-options">
              {PRIORITIES.map((p) => (
                <label key={p} className={priority === p ? 'is-selected' : ''}>
                  <input
                    type="radio"
                    name="priority"
                    value={p}
                    checked={priority === p}
                    onChange={() => setPriority(p)}
                  />
                  {p}
                </label>
              ))}
            </div>
          </fieldset>
          <button
            type="submit"
            disabled={busy || session.step !== 'awaiting_priority'}
          >
            {session.step === 'creating_incident'
              ? 'Creating incident…'
              : session.step === 'analyzing'
                ? 'Running AI triage…'
                : 'Create ServiceNow incident (mock)'}
          </button>
        </form>
      </section>
    )
  }

  return (
    <section className="panel intake-panel">
      <header className="panel__header">
        <h2>Intake complete</h2>
        <p>Issue and priority captured for this bridge.</p>
      </header>
      <dl className="kv">
        <div>
          <dt>Operator</dt>
          <dd>{session.operator}</dd>
        </div>
        <div>
          <dt>Issue</dt>
          <dd>{session.issue}</dd>
        </div>
        <div>
          <dt>Priority</dt>
          <dd>{session.priority}</dd>
        </div>
      </dl>
    </section>
  )
}
