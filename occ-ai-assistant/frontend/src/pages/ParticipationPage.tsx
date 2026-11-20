import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Loader2, RefreshCw, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  confirmAttendance,
  listAttendance,
  listBridges,
  listIncidents,
  listParticipation,
  syncBridgeAttendance,
} from '../api/client'
import type {
  BridgeAttendance,
  Incident,
  ParticipationRow,
  TeamsBridge,
} from '../types'
import { MockBadge } from '../components/MockBadge'

export function ParticipationPage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [bridges, setBridges] = useState<TeamsBridge[]>([])
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [matrix, setMatrix] = useState<ParticipationRow[]>([])
  const [attendance, setAttendance] = useState<BridgeAttendance[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const incidentBridges = useMemo(
    () =>
      selectedId
        ? bridges.filter((b) => b.incident_id === selectedId)
        : [],
    [bridges, selectedId],
  )

  async function bootstrap() {
    const [incs, br] = await Promise.all([listIncidents(), listBridges()])
    setIncidents(incs)
    setBridges(br)
    const preferred =
      incs.find((i) => i.status === 'Active' || i.bridge_active) || incs[0]
    if (preferred) setSelectedId(preferred.id)
  }

  async function refreshSelected(id: number) {
    const [part, att] = await Promise.all([
      listParticipation(id),
      listAttendance(id),
    ])
    setMatrix(part)
    setAttendance(att)
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        await bootstrap()
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
        await refreshSelected(Number(selectedId))
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  async function onSync(bridgeId: number) {
    setBusy(`sync-${bridgeId}`)
    setError(null)
    setSuccess(null)
    try {
      const rows = await syncBridgeAttendance(bridgeId)
      setSuccess(
        `Loaded ${rows.length} MOCK SAMPLE attendance row(s) (offsets from bridge started_at)`,
      )
      if (selectedId) await refreshSelected(Number(selectedId))
      setBridges(await listBridges())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setBusy(null)
    }
  }

  async function onConfirm(id: number) {
    setBusy(`confirm-${id}`)
    setError(null)
    try {
      await confirmAttendance(id)
      if (selectedId) await refreshSelected(Number(selectedId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Confirm failed')
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading participation…
      </div>
    )
  }

  const selected = incidents.find((i) => i.id === selectedId)

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Team Participation
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Distinguish PagerDuty notify / ack from Teams join and attendance confirmed.
            MOCK sample joins are labeled; timestamps are never fabricated.
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
            onChange={(e) =>
              setSelectedId(e.target.value ? Number(e.target.value) : '')
            }
          >
            <option value="">Select…</option>
            {incidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                {inc.occ_incident_id} · {inc.title} ({inc.status})
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Timeline:{' '}
            <Link
              className="text-teal-800 underline"
              to={`/timeline?incident=${selected.id}`}
            >
              view unified events
            </Link>
          </p>
        )}
      </section>

      {!!incidentBridges.length && (
        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
          <h3 className="text-sm font-semibold">Bridge attendance sync</h3>
          <p className="mt-1 text-xs text-[var(--color-muted)]">
            Graph when available; otherwise clearly labeled MOCK samples offset from{' '}
            <code>started_at</code>. Open the bridge first.
          </p>
          <ul className="mt-3 space-y-2">
            {incidentBridges.map((b) => (
              <li
                key={b.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-[var(--color-slate-line)] px-3 py-2 text-sm"
              >
                <span>
                  <span className="font-semibold">{b.bridge_code}</span>
                  <span className="ml-2 text-xs text-[var(--color-muted)]">
                    {b.status}
                    {b.started_at ? ` · started ${new Date(b.started_at).toLocaleString()}` : ' · not opened'}
                    {b.is_mock ? ' · MOCK' : ''}
                  </span>
                </span>
                <button
                  type="button"
                  disabled={busy === `sync-${b.id}` || !b.started_at}
                  onClick={() => onSync(b.id)}
                  className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
                >
                  {busy === `sync-${b.id}` ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                  Sync attendance
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="overflow-x-auto rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Participation matrix</h3>
        </div>
        {!matrix.length ? (
          <p className="px-4 py-6 text-sm text-[var(--color-muted)]">
            No participation signals yet. Approve + page teams, open a bridge, then sync attendance.
          </p>
        ) : (
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-2 font-medium">Person / team</th>
                <th className="px-4 py-2 font-medium">PD notify</th>
                <th className="px-4 py-2 font-medium">PD ack</th>
                <th className="px-4 py-2 font-medium">Teams join</th>
                <th className="px-4 py-2 font-medium">Attendance confirmed</th>
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr
                  key={`${row.team_slug}-${row.display_name}`}
                  className="border-t border-[var(--color-slate-line)]"
                >
                  <td className="px-4 py-3">
                    <p className="font-medium">{row.display_name}</p>
                    <p className="font-mono text-[10px] text-[var(--color-muted)]">
                      {row.team_name || row.team_slug || '—'}
                      {row.is_mock ? ' · MOCK' : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <Flag on={row.pd_notified} at={row.pd_notified_at} />
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <Flag on={row.pd_acknowledged} at={row.pd_acknowledged_at} />
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <Flag on={row.teams_joined} at={row.teams_joined_at} />
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <Flag on={row.attendance_confirmed} at={row.attendance_confirmed_at} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="overflow-x-auto rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Attendance records</h3>
          <Users className="h-4 w-4 text-[var(--color-accent)]" />
        </div>
        {!attendance.length ? (
          <p className="px-4 py-6 text-sm text-[var(--color-muted)]">No attendance rows yet.</p>
        ) : (
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-2 font-medium">Person</th>
                <th className="px-4 py-2 font-medium">Kind</th>
                <th className="px-4 py-2 font-medium">Joined</th>
                <th className="px-4 py-2 font-medium">Source / verify</th>
                <th className="px-4 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {attendance.map((row) => (
                <tr key={row.id} className="border-t border-[var(--color-slate-line)]">
                  <td className="px-4 py-3">
                    <p className="font-medium">{row.display_name}</p>
                    <p className="font-mono text-[10px] text-[var(--color-muted)]">
                      {row.team_name || '—'}
                      {row.is_mock ? ' · MOCK SAMPLE' : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-xs font-semibold">{row.event_kind}</td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {new Date(row.joined_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {row.source} · {row.verification_status}
                  </td>
                  <td className="px-4 py-3">
                    {row.event_kind !== 'attendance_confirmed' && (
                      <button
                        type="button"
                        disabled={busy === `confirm-${row.id}`}
                        onClick={() => onConfirm(row.id)}
                        className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
                      >
                        {busy === `confirm-${row.id}` ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3" />
                        )}
                        Confirm
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}

function Flag({ on, at }: { on: boolean; at?: string | null }) {
  if (!on) return <span className="text-[var(--color-muted)]">—</span>
  return (
    <span>
      <span className="font-semibold text-teal-800">Yes</span>
      {at && (
        <span className="mt-0.5 block font-mono text-[10px] text-[var(--color-muted)]">
          {new Date(at).toLocaleString()}
        </span>
      )}
    </span>
  )
}
