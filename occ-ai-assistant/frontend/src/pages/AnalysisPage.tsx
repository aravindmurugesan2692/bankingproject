import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Info, Loader2, RefreshCw, Sparkles } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { getIncidentAnalysis, listAnalyses, rerunAnalysis } from '../api/client'
import type { IncidentAnalysis } from '../types'
import { MockBadge } from '../components/MockBadge'

export function AnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get('incident')
  const [analyses, setAnalyses] = useState<IncidentAnalysis[]>([])
  const [selected, setSelected] = useState<IncidentAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [rerunning, setRerunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedIncidentId = useMemo(() => {
    if (selectedId) return Number(selectedId)
    return analyses[0]?.incident_id ?? null
  }, [selectedId, analyses])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const rows = await listAnalyses()
        if (!cancelled) {
          setAnalyses(rows)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load analyses')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedIncidentId) {
      setSelected(null)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const detail = await getIncidentAnalysis(selectedIncidentId)
        if (!cancelled) setSelected(detail)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load analysis')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedIncidentId])

  async function onRerun() {
    if (!selectedIncidentId) return
    setRerunning(true)
    setError(null)
    try {
      const detail = await rerunAnalysis(selectedIncidentId)
      setSelected(detail)
      const rows = await listAnalyses()
      setAnalyses(rows)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rerun failed')
    } finally {
      setRerunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading analyses…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Incident Analysis
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Structured AI hypotheses and support-team recommendations. Not confirmed root cause.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <MockBadge label="PHASE 2–3" />
          <Link
            to="/approvals"
            className="rounded-md border border-[var(--color-slate-line)] bg-white px-3.5 py-2 text-sm font-semibold hover:bg-slate-50"
          >
            Go to Approvals
          </Link>
          <Link
            to="/initiate"
            className="rounded-md bg-[var(--color-accent)] px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-800"
          >
            Initiate Incident
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {!analyses.length ? (
        <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-8 text-sm text-[var(--color-muted)] shadow-sm">
          <p className="font-medium text-[var(--color-ink)]">No analyses yet</p>
          <p className="mt-2">
            Start with{' '}
            <Link className="font-medium text-teal-800 underline" to="/initiate">
              Initiate Incident
            </Link>{' '}
            — analysis runs automatically and opens here. Seeded demo incidents also receive MOCK
            analyses on first backend start.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="animate-fade-up-delay-1 rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
            <div className="border-b border-[var(--color-slate-line)] px-4 py-3 text-sm font-semibold">
              Recent analyses
            </div>
            <ul className="max-h-[70vh] overflow-y-auto divide-y divide-[var(--color-slate-line)]">
              {analyses.map((row) => {
                const active = row.incident_id === selectedIncidentId
                return (
                  <li key={row.id}>
                    <button
                      type="button"
                      onClick={() => setSearchParams({ incident: String(row.incident_id) })}
                      className={`w-full px-4 py-3 text-left text-sm transition ${
                        active ? 'bg-teal-50' : 'hover:bg-slate-50'
                      }`}
                    >
                      <p className="font-mono text-xs text-[var(--color-muted)]">
                        {row.occ_incident_id}
                      </p>
                      <p className="mt-1 line-clamp-2 font-medium text-[var(--color-ink)]">
                        {row.incident_title}
                      </p>
                      <p className="mt-1 text-xs text-[var(--color-muted)]">
                        {row.suggested_priority} · {row.category}
                      </p>
                    </button>
                  </li>
                )
              })}
            </ul>
          </aside>

          {selected && (
            <section className="animate-fade-up-delay-2 space-y-4">
              <div className="rounded-xl border border-amber-200 bg-amber-50/90 p-4 text-sm text-amber-950">
                <div className="flex gap-2">
                  <Info className="mt-0.5 h-4 w-4 shrink-0" />
                  <p>{selected.disclaimer}</p>
                </div>
              </div>

              <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-[var(--color-muted)]">
                      {selected.occ_incident_id}
                    </p>
                    <h3 className="mt-1 text-xl font-bold text-[var(--color-ink)]">
                      {selected.incident_title}
                    </h3>
                    <p className="mt-2 text-sm text-[var(--color-muted)]">{selected.summary}</p>
                  </div>
                  <button
                    type="button"
                    onClick={onRerun}
                    disabled={rerunning}
                    className="inline-flex items-center gap-2 rounded-md border border-[var(--color-slate-line)] bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
                  >
                    {rerunning ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    Re-run analysis
                  </button>
                </div>

                <div className="mt-4 flex flex-wrap gap-2 text-xs">
                  <span className="rounded border border-teal-200 bg-teal-50 px-2 py-1 font-semibold text-teal-800">
                    {selected.suggested_priority}
                  </span>
                  <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                    {selected.category}
                  </span>
                  <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                    {selected.affected_application}
                  </span>
                  {selected.is_mock ? <MockBadge /> : (
                    <span className="inline-flex items-center gap-1 rounded border border-teal-200 bg-teal-50 px-2 py-0.5 text-teal-800">
                      <Sparkles className="h-3 w-3" /> Live LLM
                    </span>
                  )}
                  <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 font-mono">
                    {selected.provider}/{selected.model}
                  </span>
                </div>
              </div>

              {selected.needs_more_info && (
                <div className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-950">
                  <div className="flex gap-2 font-semibold">
                    <AlertTriangle className="h-4 w-4" />
                    Insufficient information — request more details before treating this as actionable
                  </div>
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <Panel title="Business impact">{selected.business_impact}</Panel>
                <Panel title="Affected application">{selected.affected_application}</Panel>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <ListPanel title="Potential technical causes" items={selected.potential_causes} />
                <ListPanel title="Missing information" items={selected.missing_information} />
                <ListPanel
                  title="Initial troubleshooting steps"
                  items={selected.troubleshooting_steps}
                />
                <ListPanel title="Suggested next actions" items={selected.next_actions} />
              </div>

              <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
                <div className="border-b border-[var(--color-slate-line)] px-4 py-3 text-sm font-semibold">
                  Recommended support teams
                </div>
                <ul className="divide-y divide-[var(--color-slate-line)]">
                  {selected.recommended_teams.map((team) => (
                    <li key={team.slug} className="px-4 py-3">
                      <p className="font-semibold text-[var(--color-ink)]">{team.team}</p>
                      <p className="mt-1 text-sm text-[var(--color-muted)]">{team.reason}</p>
                      <p className="mt-1 font-mono text-[10px] text-[var(--color-muted)]">
                        {team.slug}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
      <h4 className="text-xs font-semibold tracking-wide text-[var(--color-muted)] uppercase">
        {title}
      </h4>
      <p className="mt-2 text-sm text-[var(--color-ink)]">{children}</p>
    </div>
  )
}

function ListPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
      <h4 className="text-xs font-semibold tracking-wide text-[var(--color-muted)] uppercase">
        {title}
      </h4>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--color-ink)]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
