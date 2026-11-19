import { useEffect, useState } from 'react'
import { Loader2, Network } from 'lucide-react'
import { listTeams } from '../api/client'
import type { SupportTeam } from '../types'
import { MockBadge } from '../components/MockBadge'

export function SupportTeamsPage() {
  const [teams, setTeams] = useState<SupportTeam[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<SupportTeam | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listTeams()
        if (!cancelled) {
          setTeams(rows)
          setSelected(rows[0] ?? null)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load teams')
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
        Loading support teams…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Support Team Configuration
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Ownership, responsibilities, and PagerDuty placeholders used by AI team
            recommendations. No employee names are stored.
          </p>
        </div>
        <MockBadge label="PHASE 2 CATALOG" />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <aside className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
          <div className="border-b border-[var(--color-slate-line)] px-4 py-3 text-sm font-semibold">
            Teams ({teams.length})
          </div>
          <ul className="max-h-[70vh] divide-y divide-[var(--color-slate-line)] overflow-y-auto">
            {teams.map((team) => (
              <li key={team.id}>
                <button
                  type="button"
                  onClick={() => setSelected(team)}
                  className={`flex w-full items-start gap-2 px-4 py-3 text-left text-sm transition ${
                    selected?.id === team.id ? 'bg-teal-50' : 'hover:bg-slate-50'
                  }`}
                >
                  <Network className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-accent)]" />
                  <span>
                    <span className="block font-medium">{team.name}</span>
                    <span className="mt-0.5 block font-mono text-[10px] text-[var(--color-muted)]">
                      {team.slug}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {selected && (
          <section className="space-y-4 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 className="text-xl font-bold text-[var(--color-ink)]">{selected.name}</h3>
                <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">{selected.slug}</p>
              </div>
              <span
                className={`rounded border px-2 py-0.5 text-xs font-semibold ${
                  selected.active
                    ? 'border-teal-200 bg-teal-50 text-teal-800'
                    : 'border-slate-200 bg-slate-50 text-slate-600'
                }`}
              >
                {selected.active ? 'Active' : 'Inactive'}
              </span>
            </div>

            <Field label="Description" value={selected.description} />
            <Field label="Application ownership" value={selected.ownership} />
            <Field label="Responsibilities" value={selected.responsibilities} />

            <div className="grid gap-3 md:grid-cols-2">
              <Field
                label="PagerDuty service ID"
                value={selected.pagerduty_service_id}
                mono
              />
              <Field
                label="PagerDuty escalation policy ID"
                value={selected.pagerduty_escalation_policy_id}
                mono
              />
            </div>

            <p className="text-xs text-[var(--color-muted)]">
              Used when OCC approves an incident — ServiceNow create then PagerDuty page (MOCK by
              default). Teams bridges are Phase 5.
            </p>
          </section>
        )}
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <p className="text-xs font-semibold tracking-wide text-[var(--color-muted)] uppercase">
        {label}
      </p>
      <p className={`mt-1 text-sm text-[var(--color-ink)] ${mono ? 'font-mono text-xs' : ''}`}>
        {value}
      </p>
    </div>
  )
}
