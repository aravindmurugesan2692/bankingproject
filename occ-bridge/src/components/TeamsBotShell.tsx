import { useEffect, useMemo, useRef, useState } from 'react'
import type { BridgeSession, Priority } from '../types'

interface ChatMessage {
  id: string
  from: 'bot' | 'occ'
  text: string
}

interface Props {
  session: BridgeSession | null
  busy: boolean
  onSubmitIssue: (issue: string) => void
  onSubmitPriority: (priority: Priority) => void
  onApprove: () => void
}

const PRIORITIES: Priority[] = ['P1', 'P2', 'P3', 'P4']

/**
 * Simulated Teams bot chat UI shell.
 * Labeled as SAMPLE until Azure Bot registration exists.
 */
export function TeamsBotShell({
  session,
  busy,
  onSubmitIssue,
  onSubmitPriority,
  onApprove,
}: Props) {
  const [draft, setDraft] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  const messages = useMemo(() => buildMessages(session), [session])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, session?.step])

  const canType =
    session?.step === 'awaiting_issue' || session?.step === 'awaiting_priority'

  return (
    <section className="panel bot-shell">
      <header className="panel__header bot-shell__header">
        <div>
          <h2>Teams bot</h2>
          <p>Simulated in-browser chat — sample until Azure Bot exists.</p>
        </div>
        <span className="sample-pill">SAMPLE BOT</span>
      </header>

      {!session ? (
        <p className="empty">Open a bridge to start the bot conversation.</p>
      ) : (
        <>
          <div className="bot-thread" aria-live="polite">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`bot-bubble bot-bubble--${m.from}`}
              >
                <span className="bot-bubble__who">
                  {m.from === 'bot' ? 'Bridge Assist' : 'OCC'}
                </span>
                <p>{m.text}</p>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          {session.step === 'awaiting_priority' && (
            <div className="bot-quick">
              {PRIORITIES.map((p) => (
                <button
                  key={p}
                  type="button"
                  disabled={busy}
                  onClick={() => onSubmitPriority(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          )}

          {session.step === 'recommendations_ready' && !session.approved && (
            <div className="bot-quick">
              <button type="button" disabled={busy} onClick={onApprove}>
                Approve engagement
              </button>
            </div>
          )}

          <form
            className="bot-composer"
            onSubmit={(e) => {
              e.preventDefault()
              if (!draft.trim() || busy || !canType) return
              if (session.step === 'awaiting_issue') {
                onSubmitIssue(draft.trim())
                setDraft('')
              } else if (session.step === 'awaiting_priority') {
                const p = draft.trim().toUpperCase() as Priority
                if (PRIORITIES.includes(p)) {
                  onSubmitPriority(p)
                  setDraft('')
                }
              }
            }}
          >
            <input
              type="text"
              placeholder={
                session.step === 'awaiting_issue'
                  ? 'Describe the issue…'
                  : session.step === 'awaiting_priority'
                    ? 'Type P1–P4 or tap a button…'
                    : 'Bot awaiting console actions…'
              }
              value={draft}
              disabled={!canType || busy}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button type="submit" disabled={!canType || busy || !draft.trim()}>
              Send
            </button>
          </form>
        </>
      )}
    </section>
  )
}

function buildMessages(session: BridgeSession | null): ChatMessage[] {
  if (!session) return []

  const msgs: ChatMessage[] = [
    {
      id: 'm1',
      from: 'bot',
      text: `${session.bridgeId} bridge is open. What issue are you seeing?`,
    },
  ]

  if (session.issue) {
    msgs.push({ id: 'm2', from: 'occ', text: session.issue })
    msgs.push({
      id: 'm3',
      from: 'bot',
      text: 'Got it. What priority should we assign? (P1–P4)',
    })
  }

  if (session.priority) {
    msgs.push({ id: 'm4', from: 'occ', text: session.priority })
  }

  if (session.incident) {
    msgs.push({
      id: 'm5',
      from: 'bot',
      text: `ServiceNow incident ${session.incident.number} created (mock). Analyzing…`,
    })
  }

  if (session.recommendation) {
    msgs.push({
      id: 'm6',
      from: 'bot',
      text: `Recommend ${session.recommendation.team} team (${session.recommendation.confidence} confidence). ${session.recommendation.summary} Approve engagement to page via PagerDuty?`,
    })
  }

  if (session.approved && session.page) {
    msgs.push({
      id: 'm7',
      from: 'occ',
      text: 'Approved',
    })
    msgs.push({
      id: 'm8',
      from: 'bot',
      text: `${session.page.team} paged (${session.page.pageId}). They should join the Teams bridge shortly.`,
    })
  }

  return msgs
}
