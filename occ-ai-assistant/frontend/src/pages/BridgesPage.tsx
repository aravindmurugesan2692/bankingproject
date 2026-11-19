import { useEffect, useMemo, useState } from 'react'
import {
  ExternalLink,
  Headset,
  Loader2,
  PhoneOff,
  Play,
  Plus,
  UserPlus,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  createBridge,
  endBridge,
  inviteBridge,
  listBridges,
  listIncidents,
  openBridge,
} from '../api/client'
import type { Incident, TeamsBridge } from '../types'
import { MockBadge } from '../components/MockBadge'

const ELIGIBLE = new Set(['Approved', 'Active'])

export function BridgesPage() {
  const [bridges, setBridges] = useState<TeamsBridge[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | ''>('')

  async function refresh() {
    const [bridgeRows, incidentRows] = await Promise.all([
      listBridges(),
      listIncidents(),
    ])
    setBridges(bridgeRows)
    setIncidents(incidentRows)
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        await refresh()
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

  const eligible = useMemo(
    () => incidents.filter((i) => ELIGIBLE.has(i.status)),
    [incidents],
  )

  const openCount = bridges.filter((b) => b.status === 'open' || b.status === 'created').length
  const endedCount = bridges.filter((b) => b.status === 'ended').length

  async function onCreate() {
    if (!selectedIncidentId) {
      setError('Select an OCC-approved incident first')
      return
    }
    setBusy('create')
    setError(null)
    setSuccess(null)
    try {
      const row = await createBridge(Number(selectedIncidentId), { invite: true })
      setSuccess(
        `Created ${row.bridge_code} · meeting ${row.meeting_id}` +
          (row.is_mock ? ' (MOCK)' : '') +
          (row.invited_count ? ` · invited ${row.invited_count}` : ''),
      )
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setBusy(null)
    }
  }

  async function onOpen(id: number) {
    setBusy(`open-${id}`)
    setError(null)
    try {
      await openBridge(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Open failed')
    } finally {
      setBusy(null)
    }
  }

  async function onEnd(id: number) {
    setBusy(`end-${id}`)
    setError(null)
    try {
      await endBridge(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'End failed')
    } finally {
      setBusy(null)
    }
  }

  async function onInvite(id: number) {
    setBusy(`invite-${id}`)
    setError(null)
    try {
      const row = await inviteBridge(id)
      setSuccess(`Invited ${row.invited_count} approved responder(s) to ${row.bridge_code}`)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invite failed')
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading Teams bridges…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Teams Bridge Management
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Create or associate a Teams meeting for OCC-approved incidents. Start/end times are
            recorded only when you open or end a bridge — no fabricated attendance (Phase 6).
          </p>
        </div>
        <MockBadge label="PHASE 5" />
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

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Bridges" value={bridges.length} />
        <Stat label="Created / open" value={openCount} />
        <Stat label="Ended" value={endedCount} />
      </div>

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
        <h3 className="text-sm font-semibold">Create bridge for approved incident</h3>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Requires OCC approval first.{' '}
          <Link className="text-teal-800 underline" to="/approvals">
            Approvals
          </Link>
        </p>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <label className="min-w-[16rem] flex-1 text-xs font-medium text-[var(--color-muted)]">
            Incident
            <select
              className="mt-1 w-full rounded-md border border-[var(--color-slate-line)] bg-white px-3 py-2 text-sm text-[var(--color-ink)]"
              value={selectedIncidentId}
              onChange={(e) =>
                setSelectedIncidentId(e.target.value ? Number(e.target.value) : '')
              }
            >
              <option value="">Select…</option>
              {eligible.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.occ_incident_id} · {inc.title} ({inc.status})
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={busy === 'create' || !selectedIncidentId}
            onClick={onCreate}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-navy-800)] disabled:opacity-60"
          >
            {busy === 'create' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Create + invite
          </button>
        </div>
      </section>

      {!bridges.length ? (
        <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-8 text-sm text-[var(--color-muted)] shadow-sm">
          No Teams bridges yet. Approve an incident, then create a bridge here (MOCK by default).
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-2 font-medium">Bridge</th>
                <th className="px-4 py-2 font-medium">OCC / SN / Meeting</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Times</th>
                <th className="px-4 py-2 font-medium">Invited</th>
                <th className="px-4 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {bridges.map((row) => (
                <tr key={row.id} className="border-t border-[var(--color-slate-line)]">
                  <td className="px-4 py-3 align-top">
                    <p className="font-semibold">{row.bridge_code}</p>
                    <p className="mt-0.5 text-xs text-[var(--color-muted)] line-clamp-2">
                      {row.title}
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-[var(--color-muted)]">
                      {row.provider}
                      {row.is_mock ? ' · MOCK' : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <p className="font-mono text-xs">{row.occ_incident_id}</p>
                    <p className="mt-1 font-mono text-[10px] text-[var(--color-muted)]">
                      SN {row.servicenow_number || '—'}
                    </p>
                    <p className="mt-1 flex items-center gap-1 font-mono text-[10px]">
                      {row.meeting_id}
                      {row.meeting_url && (
                        <a
                          href={row.meeting_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-teal-800"
                          title={row.meeting_url}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </p>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <StatusChip status={row.status} />
                  </td>
                  <td className="px-4 py-3 align-top font-mono text-[10px] text-[var(--color-muted)]">
                    <p>created {formatTs(row.created_at)}</p>
                    <p>started {row.started_at ? formatTs(row.started_at) : '—'}</p>
                    <p>ended {row.ended_at ? formatTs(row.ended_at) : '—'}</p>
                  </td>
                  <td className="px-4 py-3 align-top text-xs">
                    <p className="font-medium">{row.invited_count}</p>
                    <p className="text-[10px] text-[var(--color-muted)]">
                      {row.invited_at ? `at ${formatTs(row.invited_at)}` : 'not invited yet'}
                    </p>
                    <ul className="mt-1 space-y-0.5 text-[10px] text-[var(--color-muted)]">
                      {row.invited_responders.slice(0, 4).map((r) => (
                        <li key={`${r.team_slug}-${r.name}`}>{r.name || r.team_slug}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <div className="flex flex-col gap-1.5">
                      {row.meeting_url && row.status !== 'ended' && (
                        <a
                          href={row.meeting_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50"
                        >
                          <Headset className="h-3 w-3" />
                          Open meeting
                        </a>
                      )}
                      {row.status !== 'ended' && row.status !== 'open' && (
                        <button
                          type="button"
                          disabled={busy === `open-${row.id}`}
                          onClick={() => onOpen(row.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
                        >
                          {busy === `open-${row.id}` ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Play className="h-3 w-3" />
                          )}
                          Mark open
                        </button>
                      )}
                      {row.status !== 'ended' && (
                        <button
                          type="button"
                          disabled={busy === `invite-${row.id}`}
                          onClick={() => onInvite(row.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
                        >
                          {busy === `invite-${row.id}` ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <UserPlus className="h-3 w-3" />
                          )}
                          Invite responders
                        </button>
                      )}
                      {row.status !== 'ended' && (
                        <button
                          type="button"
                          disabled={busy === `end-${row.id}`}
                          onClick={() => onEnd(row.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-red-200 bg-white px-2.5 py-1.5 text-xs font-medium text-red-800 hover:bg-red-50 disabled:opacity-60"
                        >
                          {busy === `end-${row.id}` ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <PhoneOff className="h-3 w-3" />
                          )}
                          End bridge
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium tracking-wide text-[var(--color-muted)] uppercase">
          {label}
        </p>
        <Headset className="h-4 w-4 text-[var(--color-accent)]" />
      </div>
      <p className="mt-2 font-mono text-2xl font-semibold">{value}</p>
    </div>
  )
}

function StatusChip({ status }: { status: string }) {
  const styles: Record<string, string> = {
    created: 'bg-slate-50 text-slate-800 border-slate-200',
    open: 'bg-teal-50 text-teal-900 border-teal-200',
    ended: 'bg-orange-50 text-orange-900 border-orange-200',
  }
  return (
    <span
      className={`inline-flex rounded border px-2 py-0.5 text-xs font-semibold ${styles[status] ?? 'bg-slate-50 border-slate-200'}`}
    >
      {status}
    </span>
  )
}

function formatTs(value: string) {
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}
