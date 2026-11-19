import { useEffect, useMemo, useRef, useState } from 'react'
import {
  approveEngagement,
  rejectEngagement,
  startBridge,
  submitIssue,
  submitPriority,
} from '../api/bridgeApi'
import { useActiveSession, useBridges } from '../hooks/useAppStore'
import { useAsyncAction } from '../hooks/useAsyncAction'
import type { BridgeId, BridgeSession, Priority } from '../types'
import { ErrorBanner } from './ErrorBanner'

interface ChatMessage {
  id: string
  from: 'bot' | 'occ' | 'system'
  text: string
}

const PRIORITIES: Priority[] = ['P1', 'P2', 'P3', 'P4']

/**
 * Full in-app Teams bot experience.
 * Mirrors the web console flow and shares the same session API/state.
 */
export function TeamsBot() {
  const session = useActiveSession()
  const bridges = useBridges()
  const { busy, error, run, clearError } = useAsyncAction()
  const [draft, setDraft] = useState('')
  const [rejectMode, setRejectMode] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const messages = useMemo(() => buildMessages(session), [session])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, session?.step, rejectMode])

  const canTypeIssue = session?.step === 'awaiting_issue'
  const canTypePriority = session?.step === 'awaiting_priority'
  const canDecide = session?.step === 'recommendations_ready' && !session.decision

  return (
    <section className="panel bot-full">
      <header className="panel__header bot-shell__header">
        <div>
          <h2>Teams bot</h2>
          <p>
            In-app bot mirroring the OCC console flow. Same session state —
            SAMPLE until Azure Bot registration.
          </p>
        </div>
        <span className="sample-pill">SAMPLE BOT</span>
      </header>

      <ErrorBanner message={error} onDismiss={clearError} />

      {!session ? (
        <div className="bot-start">
          <p className="empty">No active bridge. Start one from the bot:</p>
          <div className="bot-quick">
            {bridges.map((b) => (
              <button
                key={b.id}
                type="button"
                disabled={busy}
                onClick={() => run(() => startBridge(b.id))}
              >
                Open {b.id}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="bot-session-chip">
            Active: <strong>{session.bridgeId}</strong> · step{' '}
            {labelStep(session.step)}
          </div>

          <div className="bot-thread bot-thread--tall" aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`bot-bubble bot-bubble--${m.from}`}>
                <span className="bot-bubble__who">
                  {m.from === 'bot'
                    ? 'Bridge Assist'
                    : m.from === 'occ'
                      ? 'OCC'
                      : 'System'}
                </span>
                <p>{m.text}</p>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          {canTypePriority ? (
            <div className="bot-quick">
              {PRIORITIES.map((p) => (
                <button
                  key={p}
                  type="button"
                  disabled={busy}
                  onClick={() => run(() => submitPriority(p))}
                >
                  {p}
                </button>
              ))}
            </div>
          ) : null}

          {canDecide && !rejectMode ? (
            <div className="bot-quick">
              <button
                type="button"
                disabled={busy}
                onClick={() => run(() => approveEngagement())}
              >
                Approve engagement
              </button>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() => setRejectMode(true)}
              >
                Reject
              </button>
            </div>
          ) : null}

          <form
            className="bot-composer"
            onSubmit={(e) => {
              e.preventDefault()
              if (!draft.trim() || busy || !session) return

              if (canTypeIssue) {
                const text = draft.trim()
                setDraft('')
                void run(() => submitIssue(text))
                return
              }

              if (canTypePriority) {
                const p = draft.trim().toUpperCase() as Priority
                if (PRIORITIES.includes(p)) {
                  setDraft('')
                  void run(() => submitPriority(p))
                }
                return
              }

              if (rejectMode && canDecide) {
                const text = draft.trim()
                setDraft('')
                setRejectMode(false)
                void run(() => rejectEngagement(text))
              }
            }}
          >
            <input
              type="text"
              placeholder={composerPlaceholder(
                session,
                canTypeIssue,
                canTypePriority,
                rejectMode,
                canDecide,
              )}
              value={draft}
              disabled={
                busy ||
                (!canTypeIssue &&
                  !canTypePriority &&
                  !(rejectMode && canDecide))
              }
              onChange={(e) => setDraft(e.target.value)}
            />
            <button
              type="submit"
              disabled={
                busy ||
                !draft.trim() ||
                (!canTypeIssue &&
                  !canTypePriority &&
                  !(rejectMode && canDecide))
              }
            >
              Send
            </button>
          </form>
        </>
      )}
    </section>
  )
}

function composerPlaceholder(
  session: BridgeSession,
  canTypeIssue: boolean,
  canTypePriority: boolean,
  rejectMode: boolean,
  canDecide: boolean,
) {
  if (canTypeIssue) return 'Describe the issue…'
  if (canTypePriority) return 'Type P1–P4 or tap a button…'
  if (rejectMode && canDecide) return 'Type rejection reason…'
  if (session.decision) return 'Decision recorded — use console timeline…'
  return 'Use quick actions above, or continue in Workspace…'
}

function buildMessages(session: BridgeSession | null): ChatMessage[] {
  if (!session) {
    return [
      {
        id: 'welcome',
        from: 'bot',
        text: 'Welcome to OCC Bridge Assist (sample). Open STS1–STS4 to begin.',
      },
    ]
  }

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
      text: `Recommend ${session.recommendation.team} (${session.recommendation.confidence}). ${session.recommendation.summary} Approve or Reject engagement?`,
    })
  }

  if (session.decision === 'approved' && session.page) {
    msgs.push({ id: 'm7', from: 'occ', text: 'Approved' })
    msgs.push({
      id: 'm8',
      from: 'bot',
      text: `${session.page.team} paged (${session.page.pageId}). They should join the Teams bridge shortly.`,
    })
  }

  if (session.decision === 'rejected') {
    msgs.push({
      id: 'm9',
      from: 'occ',
      text: `Rejected: ${session.rejectionReason ?? 'no reason'}`,
    })
    msgs.push({
      id: 'm10',
      from: 'bot',
      text: 'Understood — no PagerDuty page sent. Continue diagnostics or end the bridge from Workspace.',
    })
  }

  return msgs
}

function labelStep(step: string) {
  return step.replaceAll('_', ' ')
}

/** Keep BridgeId type referenced for future deep-link helpers. */
export type BotBridgeId = BridgeId
