import { useEffect, useMemo, useState } from 'react'
import { Activity, Loader2, Pencil, Plus } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  createTimelineEvent,
  editTimelineEvent,
  listIncidents,
  listTimeline,
  listTimelineAudits,
} from '../api/client'
import type { Incident, TimelineEvent, TimelineEventAudit } from '../types'
import { MockBadge } from '../components/MockBadge'

const TYPE_STYLES: Record<string, string> = {
  pd_notify: 'bg-amber-50 text-amber-900 border-amber-200',
  pd_ack: 'bg-teal-50 text-teal-900 border-teal-200',
  teams_join: 'bg-sky-50 text-sky-900 border-sky-200',
  attendance_confirmed: 'bg-emerald-50 text-emerald-900 border-emerald-200',
  bridge_create: 'bg-indigo-50 text-indigo-900 border-indigo-200',
  bridge_open: 'bg-indigo-50 text-indigo-900 border-indigo-200',
  bridge_end: 'bg-orange-50 text-orange-900 border-orange-200',
  bridge_invite: 'bg-violet-50 text-violet-900 border-violet-200',
  manual: 'bg-slate-50 text-slate-800 border-slate-200',
}

export function TimelinePage() {
  const [params, setParams] = useSearchParams()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [audits, setAudits] = useState<TimelineEventAudit[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [detail, setDetail] = useState('')
  const [occurredAt, setOccurredAt] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDetail, setEditDetail] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listIncidents()
        if (cancelled) return
        setIncidents(rows)
        const fromQuery = Number(params.get('incident') || '')
        const preferred =
          rows.find((r) => r.id === fromQuery) ||
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
  }, [params])

  useEffect(() => {
    if (!selectedId) return
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listTimeline(Number(selectedId))
        if (!cancelled) setEvents(rows)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load timeline')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const selected = useMemo(
    () => incidents.find((i) => i.id === selectedId),
    [incidents, selectedId],
  )

  async function refresh() {
    if (!selectedId) return
    setEvents(await listTimeline(Number(selectedId)))
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedId || !occurredAt || !detail.trim()) {
      setError('occurred_at and detail are required — timestamps are never auto-filled')
      return
    }
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      await createTimelineEvent(Number(selectedId), {
        occurred_at: new Date(occurredAt).toISOString(),
        detail: detail.trim(),
      })
      setDetail('')
      setOccurredAt('')
      setSuccess('Manual timeline entry added')
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveEdit(id: number) {
    setBusy(true)
    setError(null)
    try {
      await editTimelineEvent(id, { detail: editDetail })
      setEditingId(null)
      setSuccess('Timeline entry edited (audit recorded)')
      await refresh()
      setAudits(await listTimelineAudits(id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Edit failed')
    } finally {
      setBusy(false)
    }
  }

  async function onShowAudits(id: number) {
    setAudits(await listTimelineAudits(id))
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading timeline…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Incident Timeline
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Unified events with verification status. PD notify/ack, Teams join, attendance
            confirmed, and manual entries — never fabricate timestamps.
          </p>
        </div>
        <MockBadge label="PHASE 6" />
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
            onChange={(e) => {
              const id = e.target.value ? Number(e.target.value) : ''
              setSelectedId(id)
              if (id) setParams({ incident: String(id) })
            }}
          >
            <option value="">Select…</option>
            {incidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                {inc.occ_incident_id} · {inc.title}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Participation:{' '}
            <Link className="text-teal-800 underline" to="/participation">
              team matrix
            </Link>
          </p>
        )}
      </section>

      <form
        onSubmit={onCreate}
        className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm space-y-3"
      >
        <h3 className="text-sm font-semibold">Add manual entry</h3>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-xs font-medium text-[var(--color-muted)]">
            Occurred at (required)
            <input
              type="datetime-local"
              required
              value={occurredAt}
              onChange={(e) => setOccurredAt(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs font-medium text-[var(--color-muted)] md:col-span-2">
            Detail
            <textarea
              required
              rows={2}
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
              placeholder="What happened — OCC-observed only"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={busy || !selectedId}
          className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Add entry
        </button>
      </form>

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Events</h3>
          <Activity className="h-4 w-4 text-[var(--color-accent)]" />
        </div>
        {!events.length ? (
          <p className="px-4 py-6 text-sm text-[var(--color-muted)]">
            No timeline events yet. Approve, page, open a bridge, or add a manual entry.
          </p>
        ) : (
          <ol className="divide-y divide-[var(--color-slate-line)]">
            {events.map((ev) => (
              <li key={ev.id} className="px-4 py-3 text-sm">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex rounded border px-2 py-0.5 text-[10px] font-semibold uppercase ${TYPE_STYLES[ev.event_type] ?? 'bg-slate-50 border-slate-200'}`}
                      >
                        {ev.event_type}
                      </span>
                      <span className="font-mono text-xs text-[var(--color-muted)]">
                        {new Date(ev.occurred_at).toLocaleString()}
                      </span>
                      {ev.is_mock && <MockBadge label="MOCK" />}
                      <span className="text-[10px] text-[var(--color-muted)]">
                        {ev.verification_status}
                      </span>
                    </div>
                    <p className="mt-1 text-[var(--color-ink)]">{ev.detail}</p>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">
                      {ev.actor || '—'}
                      {ev.team_name ? ` · ${ev.team_name}` : ''}
                      {` · ${ev.source_system}`}
                    </p>
                    {editingId === ev.id && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        <input
                          className="min-w-[16rem] flex-1 rounded-md border border-[var(--color-slate-line)] px-2 py-1.5 text-sm"
                          value={editDetail}
                          onChange={(e) => setEditDetail(e.target.value)}
                        />
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => onSaveEdit(ev.id)}
                          className="rounded-md bg-teal-800 px-3 py-1.5 text-xs font-medium text-white"
                        >
                          Save
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {ev.editable && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(ev.id)
                          setEditDetail(ev.detail)
                        }}
                        className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] px-2 py-1 text-xs"
                      >
                        <Pencil className="h-3 w-3" />
                        Edit
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onShowAudits(ev.id)}
                      className="rounded-md border border-[var(--color-slate-line)] px-2 py-1 text-xs"
                    >
                      Audit
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {!!audits.length && (
        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
          <h3 className="text-sm font-semibold">Edit audit</h3>
          <ul className="mt-2 space-y-2 text-xs text-[var(--color-muted)]">
            {audits.map((a) => (
              <li key={a.id} className="rounded border border-[var(--color-slate-line)] px-3 py-2">
                <p className="font-medium text-[var(--color-ink)]">
                  {a.actor} · {a.change_summary}
                </p>
                <p className="mt-1 font-mono">{new Date(a.created_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
