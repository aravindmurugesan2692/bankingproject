import { useEffect, useMemo, useState } from 'react'
import {
  CheckCircle2,
  FileText,
  Loader2,
  Plus,
  Send,
  Sparkles,
} from 'lucide-react'
import {
  approveBridgeNote,
  approveWorkNote,
  createBridgeNote,
  generateBridgeUpdate,
  listBridgeNotes,
  listBridgeUpdates,
  listIncidents,
  listWorkNotes,
  postWorkNote,
  previewWorkNote,
} from '../api/client'
import type {
  BridgeAIUpdate,
  BridgeNote,
  Incident,
  WorkNoteDraft,
} from '../types'
import { MockBadge } from '../components/MockBadge'

export function ReportsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [notes, setNotes] = useState<BridgeNote[]>([])
  const [updates, setUpdates] = useState<BridgeAIUpdate[]>([])
  const [workNotes, setWorkNotes] = useState<WorkNoteDraft[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')
  const [noteType, setNoteType] = useState<'manual' | 'transcript_excerpt'>(
    'transcript_excerpt',
  )
  const [noteOccurred, setNoteOccurred] = useState('')

  const selected = useMemo(
    () => incidents.find((i) => i.id === selectedId),
    [incidents, selectedId],
  )

  async function refresh(id: number) {
    const [n, u, w] = await Promise.all([
      listBridgeNotes(id),
      listBridgeUpdates(id),
      listWorkNotes(id),
    ])
    setNotes(n)
    setUpdates(u)
    setWorkNotes(w)
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listIncidents()
        if (cancelled) return
        setIncidents(rows)
        const preferred =
          rows.find((r) => r.status === 'Active' && r.servicenow_number) ||
          rows.find((r) => r.status === 'Active') ||
          rows[0]
        if (preferred) setSelectedId(preferred.id)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedId) return
    let cancelled = false
    ;(async () => {
      try {
        await refresh(Number(selectedId))
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  async function onAddNote(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedId || !noteContent.trim()) return
    setBusy('note')
    setError(null)
    setSuccess(null)
    try {
      await createBridgeNote(Number(selectedId), {
        title: noteTitle,
        content: noteContent.trim(),
        note_type: noteType,
        approve_now: true,
        occurred_at: noteOccurred
          ? new Date(noteOccurred).toISOString()
          : undefined,
      })
      setNoteContent('')
      setNoteTitle('')
      setNoteOccurred('')
      setSuccess('OCC-approved bridge note added (AI may use this source only)')
      await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add note')
    } finally {
      setBusy(null)
    }
  }

  async function onGenerate() {
    if (!selectedId) return
    setBusy('generate')
    setError(null)
    setSuccess(null)
    try {
      const row = await generateBridgeUpdate(Number(selectedId))
      setSuccess(
        `AI bridge update generated · root cause: ${row.root_cause_status}` +
          (row.is_mock ? ' (MOCK)' : ''),
      )
      await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generate failed')
    } finally {
      setBusy(null)
    }
  }

  async function onPreview(updateId: number) {
    setBusy(`preview-${updateId}`)
    setError(null)
    try {
      await previewWorkNote(updateId)
      setSuccess('Work-note preview ready — OCC must approve before posting')
      if (selectedId) await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview failed')
    } finally {
      setBusy(null)
    }
  }

  async function onApproveNote(id: number) {
    setBusy(`approve-note-${id}`)
    try {
      await approveBridgeNote(id)
      if (selectedId) await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve note failed')
    } finally {
      setBusy(null)
    }
  }

  async function onApproveDraft(id: number) {
    setBusy(`approve-${id}`)
    setError(null)
    try {
      await approveWorkNote(id)
      setSuccess('Work note approved by OCC')
      if (selectedId) await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve failed')
    } finally {
      setBusy(null)
    }
  }

  async function onPost(id: number) {
    setBusy(`post-${id}`)
    setError(null)
    try {
      const result = await postWorkNote(id)
      setSuccess(
        result.duplicate
          ? `Duplicate skipped (${result.draft.status})`
          : `Posted to ServiceNow ${result.draft.servicenow_number}` +
              (result.is_mock ? ' (MOCK)' : ''),
      )
      if (selectedId) await refresh(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Post failed')
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading AI reports…
      </div>
    )
  }

  const latestUpdate = updates[0]

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            AI Incident Reports
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Bridge assistant uses only OCC-approved transcripts/manual notes — no fabricated
            activities. Work notes preview first; post to ServiceNow only after OCC approve.
          </p>
        </div>
        <MockBadge label="PHASE 7" />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900">
          {success}
        </div>
      )}

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
        <label className="text-xs font-medium text-[var(--color-muted)]">
          Incident
          <select
            className="mt-1 w-full max-w-xl rounded-md border border-[var(--color-slate-line)] bg-white px-3 py-2 text-sm"
            value={selectedId}
            onChange={(e) =>
              setSelectedId(e.target.value ? Number(e.target.value) : '')
            }
          >
            <option value="">Select…</option>
            {incidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                {inc.occ_incident_id} · {inc.title}
                {inc.servicenow_number ? ` · ${inc.servicenow_number}` : ''}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            SN {selected.servicenow_number || '—'} · status {selected.status}
          </p>
        )}
      </section>

      <form
        onSubmit={onAddNote}
        className="space-y-3 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm"
      >
        <h3 className="text-sm font-semibold">Add OCC-approved bridge note / transcript</h3>
        <p className="text-xs text-[var(--color-muted)]">
          Content must be OCC-supplied. AI will not invent bridge activities.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-xs font-medium text-[var(--color-muted)]">
            Type
            <select
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
              value={noteType}
              onChange={(e) =>
                setNoteType(e.target.value as 'manual' | 'transcript_excerpt')
              }
            >
              <option value="transcript_excerpt">Transcript excerpt</option>
              <option value="manual">Manual note</option>
            </select>
          </label>
          <label className="text-xs font-medium text-[var(--color-muted)]">
            Occurred at (optional, OCC-provided)
            <input
              type="datetime-local"
              value={noteOccurred}
              onChange={(e) => setNoteOccurred(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs font-medium text-[var(--color-muted)] md:col-span-2">
            Title
            <input
              value={noteTitle}
              onChange={(e) => setNoteTitle(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs font-medium text-[var(--color-muted)] md:col-span-2">
            Content
            <textarea
              required
              rows={4}
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
              placeholder="Paste approved transcript excerpt or OCC manual note…"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={busy === 'note' || !selectedId}
          className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {busy === 'note' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Add + approve note
        </button>
      </form>

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Approved sources</h3>
          <button
            type="button"
            disabled={busy === 'generate' || !selectedId}
            onClick={onGenerate}
            className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
          >
            {busy === 'generate' ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Sparkles className="h-3 w-3" />
            )}
            Generate AI bridge update
          </button>
        </div>
        <ul className="divide-y divide-[var(--color-slate-line)]">
          {!notes.length && (
            <li className="px-4 py-6 text-sm text-[var(--color-muted)]">
              No bridge notes yet.
            </li>
          )}
          {notes.map((n) => (
            <li key={n.id} className="px-4 py-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{n.title || n.note_type}</span>
                <span className="text-[10px] uppercase text-[var(--color-muted)]">
                  {n.status}
                </span>
                {n.is_mock && <MockBadge label="MOCK" />}
              </div>
              <p className="mt-1 whitespace-pre-wrap text-[var(--color-ink)]">{n.content}</p>
              {n.status !== 'approved' && (
                <button
                  type="button"
                  className="mt-2 text-xs font-medium text-teal-800 underline"
                  onClick={() => onApproveNote(n.id)}
                >
                  Approve for AI use
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>

      {latestUpdate && (
        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">Latest AI bridge update</h3>
            <div className="flex items-center gap-2">
              <span className="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-900">
                Root cause: {latestUpdate.root_cause_status}
              </span>
              {latestUpdate.is_mock && <MockBadge />}
            </div>
          </div>
          <p className="text-sm text-amber-900/90">{latestUpdate.disclaimer}</p>
          <p className="text-sm">{latestUpdate.summary}</p>
          <div className="grid gap-3 md:grid-cols-2">
            <ListBlock title="Key points" items={latestUpdate.key_points} />
            <ListBlock title="Hypotheses (unconfirmed)" items={latestUpdate.hypotheses} />
            <ListBlock title="Open questions" items={latestUpdate.open_questions} />
            <ListBlock title="Next actions" items={latestUpdate.next_actions} />
          </div>
          <button
            type="button"
            disabled={busy === `preview-${latestUpdate.id}`}
            onClick={() => onPreview(latestUpdate.id)}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--color-slate-line)] bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
          >
            {busy === `preview-${latestUpdate.id}` ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            Preview ServiceNow work note
          </button>
        </section>
      )}

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Work notes</h3>
          <p className="mt-1 text-xs text-[var(--color-muted)]">
            Preview → OCC approve → post (deduped). Never posts without approval.
          </p>
        </div>
        {!workNotes.length ? (
          <p className="px-4 py-6 text-sm text-[var(--color-muted)]">No work-note drafts yet.</p>
        ) : (
          <ul className="divide-y divide-[var(--color-slate-line)]">
            {workNotes.map((d) => (
              <li key={d.id} className="px-4 py-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-semibold uppercase">{d.status}</span>
                    <span className="ml-2 font-mono text-xs text-[var(--color-muted)]">
                      {d.servicenow_number || '—'} · {d.content_hash.slice(0, 10)}
                      {d.is_mock ? ' · MOCK' : ''}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    {d.status === 'preview' && (
                      <button
                        type="button"
                        disabled={busy === `approve-${d.id}`}
                        onClick={() => onApproveDraft(d.id)}
                        className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] px-2 py-1 text-xs"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        Approve
                      </button>
                    )}
                    {d.status === 'approved' && (
                      <button
                        type="button"
                        disabled={busy === `post-${d.id}`}
                        onClick={() => onPost(d.id)}
                        className="inline-flex items-center gap-1 rounded-md bg-teal-800 px-2 py-1 text-xs font-medium text-white"
                      >
                        <Send className="h-3 w-3" />
                        Post to SN
                      </button>
                    )}
                  </div>
                </div>
                <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded border border-[var(--color-slate-line)] bg-[var(--color-slate-panel)] p-3 text-[11px]">
                  {d.content}
                </pre>
                {d.posted_at && (
                  <p className="mt-1 text-[10px] text-[var(--color-muted)]">
                    Posted {new Date(d.posted_at).toLocaleString()} by {d.posted_by}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded border border-[var(--color-slate-line)] p-3">
      <p className="text-xs font-semibold uppercase text-[var(--color-muted)]">{title}</p>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
        {items.map((item) => (
          <li key={item.slice(0, 48)}>{item}</li>
        ))}
        {!items.length && <li className="text-[var(--color-muted)]">—</li>}
      </ul>
    </div>
  )
}
