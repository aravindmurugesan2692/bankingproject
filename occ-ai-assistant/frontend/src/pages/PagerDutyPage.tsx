import { useEffect, useState } from 'react'
import { Bell, CheckCircle2, ExternalLink, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { acknowledgePagerDuty, listPagerDutyNotifications } from '../api/client'
import type { PagerDutyNotification } from '../types'
import { MockBadge } from '../components/MockBadge'

export function PagerDutyPage() {
  const [rows, setRows] = useState<PagerDutyNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [acking, setAcking] = useState<number | null>(null)

  async function refresh() {
    const data = await listPagerDutyNotifications()
    setRows(data)
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

  async function onAck(id: number) {
    setAcking(id)
    setError(null)
    try {
      await acknowledgePagerDuty(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Acknowledge failed')
    } finally {
      setAcking(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading PagerDuty notifications…
      </div>
    )
  }

  const notified = rows.filter((r) => r.escalation_status === 'notified' && !r.acknowledged_at)
  const acknowledged = rows.filter((r) => r.escalation_status === 'acknowledged')

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">PagerDuty</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Notification and acknowledgement status for approved incidents. Teams are never paged
            without explicit OCC approval.
          </p>
        </div>
        <MockBadge label="PHASE 4" />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Total pages" value={rows.length} />
        <Stat label="Awaiting ack" value={notified.length} />
        <Stat label="Acknowledged" value={acknowledged.length} />
      </div>

      {!rows.length ? (
        <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-8 text-sm text-[var(--color-muted)] shadow-sm">
          No PagerDuty notifications yet.{' '}
          <Link className="font-medium text-teal-800 underline" to="/approvals">
            Approve an incident
          </Link>{' '}
          to page selected teams (MOCK by default).
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-2 font-medium">OCC / SN / PD</th>
                <th className="px-4 py-2 font-medium">Team</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Notified</th>
                <th className="px-4 py-2 font-medium">Acknowledged</th>
                <th className="px-4 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-[var(--color-slate-line)]">
                  <td className="px-4 py-3 align-top">
                    <p className="font-mono text-xs">
                      <Link
                        className="text-teal-800 underline"
                        to={`/approvals?incident=${row.incident_id}`}
                      >
                        {row.occ_incident_id}
                      </Link>
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-[var(--color-muted)]">
                      SN {row.servicenow_number || '—'}
                    </p>
                    <p className="mt-1 flex items-center gap-1 font-mono text-[10px]">
                      {row.pd_incident_id}
                      {row.is_mock && <span className="text-amber-700">MOCK</span>}
                      {row.pd_incident_url && (
                        <a
                          href={row.pd_incident_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-teal-800"
                          title={row.pd_incident_url}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </p>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <p className="font-medium">{row.team_name}</p>
                    <p className="font-mono text-[10px] text-[var(--color-muted)]">
                      {row.pagerduty_service_id}
                    </p>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <StatusChip status={row.escalation_status} />
                  </td>
                  <td className="px-4 py-3 align-top font-mono text-xs text-[var(--color-muted)]">
                    {formatTs(row.notified_at)}
                  </td>
                  <td className="px-4 py-3 align-top font-mono text-xs text-[var(--color-muted)]">
                    {row.acknowledged_at ? formatTs(row.acknowledged_at) : '—'}
                  </td>
                  <td className="px-4 py-3 align-top">
                    {!row.acknowledged_at && (
                      <button
                        type="button"
                        disabled={acking === row.id}
                        onClick={() => onAck(row.id)}
                        className="inline-flex items-center gap-1 rounded-md border border-[var(--color-slate-line)] bg-white px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-60"
                      >
                        {acking === row.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3" />
                        )}
                        Record ack
                      </button>
                    )}
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
        <Bell className="h-4 w-4 text-[var(--color-accent)]" />
      </div>
      <p className="mt-2 font-mono text-2xl font-semibold">{value}</p>
    </div>
  )
}

function StatusChip({ status }: { status: string }) {
  const styles: Record<string, string> = {
    notified: 'bg-amber-50 text-amber-900 border-amber-200',
    acknowledged: 'bg-teal-50 text-teal-900 border-teal-200',
    escalated: 'bg-orange-50 text-orange-900 border-orange-200',
    failed: 'bg-red-50 text-red-800 border-red-200',
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
