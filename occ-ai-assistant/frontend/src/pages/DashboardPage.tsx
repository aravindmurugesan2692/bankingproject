import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Headset,
  Loader2,
  ShieldAlert,
  Timer,
  Activity,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { fetchDashboard } from '../api/client'
import type { DashboardBundle } from '../types'
import { MockBadge } from '../components/MockBadge'
import { PriorityBadge } from '../components/PriorityBadge'
import { StatusBadge } from '../components/StatusBadge'

function formatMinutes(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '—'
  return `${value} min`
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardBundle | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const bundle = await fetchDashboard()
        if (!cancelled) {
          setData(bundle)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading dashboard…
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
        {error ?? 'No dashboard data'}
        <p className="mt-2 text-xs">
          Ensure the FastAPI backend is running on port 8000, then refresh.
        </p>
      </div>
    )
  }

  const { summary } = data
  const cards = [
    { label: 'Total incidents', value: summary.total_incidents, icon: Activity },
    { label: 'Active incidents', value: summary.active_incidents, icon: ShieldAlert },
    { label: 'Critical incidents', value: summary.critical_incidents, icon: AlertTriangle },
    { label: 'Pending approvals', value: summary.pending_approvals, icon: Clock3 },
    { label: 'Active bridges', value: summary.active_bridges, icon: Headset },
    { label: 'Resolved incidents', value: summary.resolved_incidents, icon: CheckCircle2 },
    { label: 'Avg acknowledgement', value: formatMinutes(summary.avg_ack_minutes), icon: Timer },
    {
      label: 'Avg resolution',
      value: formatMinutes(summary.avg_resolution_minutes),
      icon: CheckCircle2,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">Dashboard</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Enterprise OCC overview. Seeded sample rows are labeled as mock data.
          </p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Workflow:{' '}
            <Link className="font-medium text-teal-800 underline" to="/initiate">
              Initiate
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/analysis">
              AI Analysis
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/teams-config">
              Support teams
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/approvals">
              Approvals
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/pagerduty">
              PagerDuty
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/bridges">
              Teams bridges
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/participation">
              Participation
            </Link>{' '}
            →{' '}
            <Link className="font-medium text-teal-800 underline" to="/timeline">
              Timeline
            </Link>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <MockBadge label={data.data_label} />
          <Link
            to="/initiate"
            className="rounded-md bg-[var(--color-accent)] px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800"
          >
            Initiate Incident
          </Link>
        </div>
      </div>

      <div className="animate-fade-up-delay-1 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <div
              key={card.label}
              className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <p className="text-xs font-medium tracking-wide text-[var(--color-muted)] uppercase">
                  {card.label}
                </p>
                <Icon className="h-4 w-4 text-[var(--color-accent)]" />
              </div>
              <p className="mt-3 font-mono text-2xl font-semibold text-[var(--color-ink)]">
                {card.value}
              </p>
            </div>
          )
        })}
      </div>

      <div className="animate-fade-up-delay-2 grid gap-4 xl:grid-cols-3">
        <section className="xl:col-span-2 rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">Active incidents</h3>
            <MockBadge />
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
                <tr>
                  <th className="px-4 py-2 font-medium">ID</th>
                  <th className="px-4 py-2 font-medium">Title</th>
                  <th className="px-4 py-2 font-medium">Priority</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Service</th>
                </tr>
              </thead>
              <tbody>
                {data.active_incidents.map((incident) => (
                  <tr key={incident.id} className="border-t border-[var(--color-slate-line)]">
                    <td className="px-4 py-2.5 font-mono text-xs">
                      <Link
                        className="text-teal-800 underline-offset-2 hover:underline"
                        to={`/analysis?incident=${incident.id}`}
                      >
                        {incident.occ_incident_id}
                      </Link>
                      {incident.is_mock && (
                        <span className="ml-1 text-[10px] text-amber-700">MOCK</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 max-w-xs truncate">
                      <Link
                        className="hover:text-teal-800"
                        to={`/analysis?incident=${incident.id}`}
                      >
                        {incident.title}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5">
                      <PriorityBadge priority={incident.priority} />
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={incident.status} />
                    </td>
                    <td className="px-4 py-2.5 text-[var(--color-muted)]">
                      {incident.application_service}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">Priority distribution</h3>
            <MockBadge />
          </div>
          <ul className="space-y-3 p-4">
            {Object.entries(data.priority_distribution).map(([priority, count]) => (
              <li key={priority} className="flex items-center justify-between text-sm">
                <PriorityBadge priority={priority} />
                <span className="font-mono font-semibold">{count}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">Active Teams bridges</h3>
            <Link to="/bridges" className="text-xs font-medium text-teal-800 underline">
              Manage
            </Link>
          </div>
          <ul className="divide-y divide-[var(--color-slate-line)]">
            {data.active_bridges.map((bridge) => (
              <li key={`${bridge.bridge}-${bridge.incident_id}-${bridge.bridge_id || ''}`} className="px-4 py-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[var(--color-ink)]">{bridge.bridge}</span>
                  <span className="inline-flex items-center gap-1 text-xs text-teal-700">
                    <span className="live-dot h-1.5 w-1.5 rounded-full bg-teal-600" />
                    {bridge.status}
                  </span>
                </div>
                <p className="mt-1 text-[var(--color-muted)]">{bridge.title}</p>
                <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">
                  {bridge.incident_id} · {bridge.participants} invited
                  {bridge.mock ? ' · MOCK' : ''}
                </p>
              </li>
            ))}
            {!data.active_bridges.length && (
              <li className="px-4 py-3 text-sm text-[var(--color-muted)]">No active bridges</li>
            )}
          </ul>
        </section>

        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">Recent activities</h3>
            <MockBadge />
          </div>
          <ul className="divide-y divide-[var(--color-slate-line)]">
            {data.recent_activities.map((activity) => (
              <li key={`${activity.time}-${activity.detail}`} className="px-4 py-3 text-sm">
                <p className="text-[var(--color-ink)]">{activity.detail}</p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">
                  {activity.actor} · {activity.time}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">Pending acknowledgements</h3>
            <Link to="/pagerduty" className="text-xs font-medium text-teal-800 underline">
              PagerDuty
            </Link>
          </div>
          <ul className="divide-y divide-[var(--color-slate-line)]">
            {data.pending_acknowledgements.map((row) => (
              <li key={`${row.team}-${row.incident_id}-${row.pd_incident_id || ''}`} className="px-4 py-3 text-sm">
                <p className="font-medium">{row.team}</p>
                <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">
                  {row.incident_id} · waiting {row.wait_minutes} min
                  {row.pd_incident_id ? ` · ${row.pd_incident_id}` : ''}
                  {row.mock ? ' · MOCK' : ''}
                </p>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {(data.pagerduty_notifications?.length ?? 0) > 0 && (
        <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
            <h3 className="text-sm font-semibold">PagerDuty notification status</h3>
            <MockBadge />
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
                <tr>
                  <th className="px-4 py-2 font-medium">OCC</th>
                  <th className="px-4 py-2 font-medium">SN</th>
                  <th className="px-4 py-2 font-medium">Team</th>
                  <th className="px-4 py-2 font-medium">PD ID</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.pagerduty_notifications!.slice(0, 8).map((row) => (
                  <tr key={row.id} className="border-t border-[var(--color-slate-line)]">
                    <td className="px-4 py-2 font-mono text-xs">{row.occ_incident_id}</td>
                    <td className="px-4 py-2 font-mono text-xs">{row.servicenow_number || '—'}</td>
                    <td className="px-4 py-2">{row.team_name}</td>
                    <td className="px-4 py-2 font-mono text-xs">
                      {row.pd_incident_id}
                      {row.is_mock && <span className="ml-1 text-amber-700">MOCK</span>}
                    </td>
                    <td className="px-4 py-2 text-xs font-semibold">{row.escalation_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--color-slate-line)] px-4 py-3">
          <h3 className="text-sm font-semibold">Recent incidents</h3>
          <MockBadge />
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-slate-panel)] text-xs text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-2 font-medium">ID</th>
                <th className="px-4 py-2 font-medium">Title</th>
                <th className="px-4 py-2 font-medium">Env</th>
                <th className="px-4 py-2 font-medium">Users</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Created by</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_incidents.map((incident) => (
                <tr key={incident.id} className="border-t border-[var(--color-slate-line)]">
                  <td className="px-4 py-2.5 font-mono text-xs">{incident.occ_incident_id}</td>
                  <td className="px-4 py-2.5">{incident.title}</td>
                  <td className="px-4 py-2.5">{incident.environment}</td>
                  <td className="px-4 py-2.5 font-mono">{incident.users_affected}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={incident.status} />
                  </td>
                  <td className="px-4 py-2.5 text-[var(--color-muted)]">{incident.created_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
