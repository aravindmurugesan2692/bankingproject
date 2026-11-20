import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CheckCircle2,
  ClipboardList,
  Loader2,
  Save,
  Search,
  Send,
  XCircle,
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import {
  approveClosure,
  fetchReportingMetrics,
  getManagementDetail,
  openClosure,
  rejectClosure,
  searchManagementHistory,
  submitClosure,
  updateClosure,
} from '../api/client'
import type {
  IncidentClosure,
  ManagementDetail,
  ManagementHistoryItem,
  ReportingMetrics,
} from '../types'
import { MockBadge } from '../components/MockBadge'
import { PriorityBadge } from '../components/PriorityBadge'
import { StatusBadge } from '../components/StatusBadge'

const ACTOR = 'OCC Engineer · Demo User'

function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function fromLocalInput(local: string): string | null {
  if (!local) return null
  const d = new Date(local)
  if (Number.isNaN(d.getTime())) return null
  return d.toISOString()
}

export function ManagementPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [items, setItems] = useState<ManagementHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [dataLabel, setDataLabel] = useState('')
  const [metrics, setMetrics] = useState<ReportingMetrics | null>(null)
  const [detail, setDetail] = useState<ManagementDetail | null>(null)
  const [closure, setClosure] = useState<IncidentClosure | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [environment, setEnvironment] = useState('')
  const [severity, setSeverity] = useState('')

  const [restoredAt, setRestoredAt] = useState('')
  const [finalSummary, setFinalSummary] = useState('')
  const [timelineSummary, setTimelineSummary] = useState('')
  const [teamNotes, setTeamNotes] = useState('')
  const [remediationNotes, setRemediationNotes] = useState('')
  const [rcaStatus, setRcaStatus] = useState<'unconfirmed' | 'confirmed'>('unconfirmed')
  const [rcaStatement, setRcaStatement] = useState('')

  const selectedId = useMemo(() => {
    const raw = searchParams.get('incident')
    return raw ? Number(raw) : null
  }, [searchParams])

  const loadHistory = useCallback(async () => {
    const res = await searchManagementHistory({
      q: q || undefined,
      status: status || undefined,
      environment: environment || undefined,
      severity: severity || undefined,
      limit: 80,
    })
    setItems(res.items)
    setTotal(res.total)
    setDataLabel(res.data_label)
  }, [q, status, environment, severity])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [_, m] = await Promise.all([
          loadHistory(),
          fetchReportingMetrics(),
        ])
        if (!cancelled) setMetrics(m)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [loadHistory])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setClosure(null)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const d = await getManagementDetail(selectedId)
        if (cancelled) return
        setDetail(d)
        const c = d.closure
        setClosure(c)
        if (c) {
          setRestoredAt(toLocalInput(c.restored_at))
          setFinalSummary(c.final_summary || '')
          setTimelineSummary(c.timeline_summary || '')
          setTeamNotes(c.team_notes || '')
          setRemediationNotes(c.remediation_notes || '')
          setRcaStatus((c.rca_status as 'unconfirmed' | 'confirmed') || 'unconfirmed')
          setRcaStatement(c.rca_statement || '')
        } else {
          setRestoredAt('')
          setFinalSummary('')
          setTimelineSummary('')
          setTeamNotes('')
          setRemediationNotes('')
          setRcaStatus('unconfirmed')
          setRcaStatement('')
        }
        setRejectReason('')
        setError(null)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load detail')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  function selectIncident(id: number) {
    setSearchParams({ incident: String(id) })
    setSuccess(null)
  }

  async function onSearch(e: React.FormEvent) {
    e.preventDefault()
    setBusy('search')
    setError(null)
    try {
      await loadHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setBusy(null)
    }
  }

  async function onOpenClosure() {
    if (!selectedId) return
    setBusy('open')
    setError(null)
    try {
      const c = await openClosure(selectedId, ACTOR)
      setClosure(c)
      setRestoredAt(toLocalInput(c.restored_at))
      setFinalSummary(c.final_summary || '')
      setTimelineSummary(c.timeline_summary || '')
      setTeamNotes(c.team_notes || '')
      setRemediationNotes(c.remediation_notes || '')
      setRcaStatus((c.rca_status as 'unconfirmed' | 'confirmed') || 'unconfirmed')
      setRcaStatement(c.rca_statement || '')
      setSuccess('Closure draft opened. Restore time must be OCC-provided.')
      await loadHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open closure')
    } finally {
      setBusy(null)
    }
  }

  async function onSaveDraft() {
    if (!closure) return
    setBusy('save')
    setError(null)
    try {
      const c = await updateClosure(closure.id, {
        restored_at: fromLocalInput(restoredAt),
        final_summary: finalSummary,
        timeline_summary: timelineSummary,
        team_notes: teamNotes,
        remediation_notes: remediationNotes,
        rca_status: rcaStatus,
        rca_statement: rcaStatement,
        actor: ACTOR,
      })
      setClosure(c)
      setSuccess('Closure draft saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setBusy(null)
    }
  }

  async function onSubmit() {
    if (!closure) return
    setBusy('submit')
    setError(null)
    try {
      await updateClosure(closure.id, {
        restored_at: fromLocalInput(restoredAt),
        final_summary: finalSummary,
        timeline_summary: timelineSummary,
        team_notes: teamNotes,
        remediation_notes: remediationNotes,
        rca_status: rcaStatus,
        rca_statement: rcaStatement,
        actor: ACTOR,
      })
      const c = await submitClosure(closure.id, ACTOR)
      setClosure(c)
      setSuccess('Submitted for OCC approval — SN/PD sync blocked until approve.')
      await loadHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submit failed')
    } finally {
      setBusy(null)
    }
  }

  async function onApprove() {
    if (!closure) return
    setBusy('approve')
    setError(null)
    try {
      const c = await approveClosure(closure.id, ACTOR, true)
      setClosure(c)
      const d = await getManagementDetail(c.incident_id)
      setDetail(d)
      setSuccess(
        'OCC approved closure. ServiceNow resolve + PagerDuty sync completed (MOCK unless live).',
      )
      await loadHistory()
      if (metrics) setMetrics(await fetchReportingMetrics())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve failed')
    } finally {
      setBusy(null)
    }
  }

  async function onReject() {
    if (!closure || !rejectReason.trim()) {
      setError('Rejection reason is required')
      return
    }
    setBusy('reject')
    setError(null)
    try {
      const c = await rejectClosure(closure.id, rejectReason, ACTOR)
      setClosure(c)
      setSuccess('Closure rejected — edit draft and resubmit.')
      await loadHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reject failed')
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading incident management…
      </div>
    )
  }

  const editable = closure && (closure.status === 'draft' || closure.status === 'rejected')
  const pending = closure?.status === 'pending_occ'

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--color-navy-900)]">
            Incident Management
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            History, reporting metrics, and OCC-gated closure — never close on AI alone.
          </p>
        </div>
        {dataLabel && <MockBadge label={dataLabel} />}
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {success}
        </div>
      )}

      {metrics && (
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Reporting metrics
            </h2>
            <MockBadge label={metrics.data_label} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: 'Total', value: metrics.total_incidents },
              { label: 'Closed / resolved', value: metrics.closed_count },
              { label: 'Pending closures', value: metrics.pending_closure_count },
              {
                label: 'Avg ack / resolve',
                value: `${metrics.avg_ack_minutes ?? '—'} / ${metrics.avg_resolution_minutes ?? '—'} min`,
              },
            ].map((c) => (
              <div key={c.label} className="rounded-lg bg-slate-50 px-3 py-2">
                <div className="text-xs text-slate-500">{c.label}</div>
                <div className="text-lg font-semibold text-[var(--color-navy-900)]">
                  {c.value}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <MetricList
              title="By category"
              rows={metrics.by_category.map((r) => [r.category, r.count])}
            />
            <MetricList
              title="By application"
              rows={metrics.volume_by_application.map((r) => [r.application, r.count])}
            />
            <MetricList
              title="By severity"
              rows={metrics.volume_by_severity.map((r) => [r.severity, r.count])}
            />
          </div>
          {metrics.repeat_incidents.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">
                Repeat incidents
              </h3>
              <ul className="space-y-1 text-sm">
                {metrics.repeat_incidents.slice(0, 5).map((r) => (
                  <li key={r.key} className="flex flex-wrap gap-2 text-slate-700">
                    <span className="font-medium">{r.sample_title}</span>
                    <span className="text-slate-400">×{r.count}</span>
                    {r.includes_mock && <MockBadge label="MOCK" />}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <section className="space-y-3">
          <form
            onSubmit={onSearch}
            className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm"
          >
            <div className="relative min-w-[12rem] flex-1">
              <Search className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search OCC ID, SN#, title…"
                className="w-full rounded-md border border-slate-200 py-2 pl-8 pr-3 text-sm"
              />
            </div>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded-md border border-slate-200 px-2 py-2 text-sm"
            >
              <option value="">All statuses</option>
              {['New', 'Analyzed', 'Pending Approval', 'Active', 'Resolved', 'Closed', 'Rejected'].map(
                (s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ),
              )}
            </select>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="rounded-md border border-slate-200 px-2 py-2 text-sm"
            >
              <option value="">All envs</option>
              {['Production', 'QA', 'Development'].map((e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              ))}
            </select>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="rounded-md border border-slate-200 px-2 py-2 text-sm"
            >
              <option value="">All severities</option>
              {['P1', 'P2', 'P3', 'P4'].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={busy === 'search'}
              className="inline-flex items-center gap-1 rounded-md bg-[var(--color-navy-900)] px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {busy === 'search' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Filter
            </button>
          </form>

          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-3 py-2 text-xs text-slate-500">
              {total} incident{total === 1 ? '' : 's'}
            </div>
            <ul className="max-h-[32rem] divide-y divide-slate-100 overflow-y-auto">
              {items.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    onClick={() => selectIncident(row.id)}
                    className={`flex w-full flex-col gap-1 px-3 py-3 text-left hover:bg-slate-50 ${
                      selectedId === row.id ? 'bg-slate-50' : ''
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-slate-500">
                        {row.occ_incident_id}
                      </span>
                      {row.servicenow_number && (
                        <span className="font-mono text-xs text-slate-400">
                          {row.servicenow_number}
                        </span>
                      )}
                      <StatusBadge status={row.status} />
                      <PriorityBadge
                        priority={row.working_severity || row.priority}
                      />
                      {row.is_mock && <MockBadge label="MOCK" />}
                    </div>
                    <div className="text-sm font-medium text-[var(--color-navy-900)]">
                      {row.title}
                    </div>
                    <div className="text-xs text-slate-500">
                      {row.application_service} · {row.environment}
                      {row.closure_status ? ` · closure: ${row.closure_status}` : ''}
                    </div>
                  </button>
                </li>
              ))}
              {items.length === 0 && (
                <li className="px-3 py-8 text-center text-sm text-slate-500">
                  No incidents match filters.
                </li>
              )}
            </ul>
          </div>
        </section>

        <section className="space-y-4">
          {!detail ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              Select an incident to view detail and run closure.
            </div>
          ) : (
            <>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-semibold text-[var(--color-navy-900)]">
                    {detail.incident.title}
                  </h2>
                  {detail.is_mock && <MockBadge label={detail.data_label} />}
                </div>
                <dl className="grid gap-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-slate-500">OCC ID</dt>
                    <dd className="font-mono">{detail.incident.occ_incident_id}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">ServiceNow</dt>
                    <dd className="font-mono">
                      {detail.incident.servicenow_number || '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">PagerDuty IDs</dt>
                    <dd className="font-mono text-xs">
                      {detail.pagerduty_incident_ids.join(', ') || '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Teams</dt>
                    <dd>{detail.assigned_teams.join(', ') || '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Ack / resolve</dt>
                    <dd>
                      {detail.incident.ack_minutes ?? '—'} /{' '}
                      {detail.incident.resolution_minutes ?? '—'} min
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Bridge duration</dt>
                    <dd>
                      {detail.bridge_duration_minutes != null
                        ? `${detail.bridge_duration_minutes} min`
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Category</dt>
                    <dd>{detail.analysis_category || '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Timeline events</dt>
                    <dd>{detail.timeline_event_count}</dd>
                  </div>
                </dl>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                    <ClipboardList className="h-4 w-4" />
                    Closure automation
                  </h3>
                  {closure && (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                      {closure.status}
                    </span>
                  )}
                </div>

                {!closure && (
                  <div className="space-y-3">
                    <p className="text-sm text-slate-600">
                      Open a closure draft after service recovery. Restore time is never
                      fabricated; SN resolve and PD sync run only after OCC approve.
                    </p>
                    <button
                      type="button"
                      onClick={onOpenClosure}
                      disabled={!!busy}
                      className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                    >
                      {busy === 'open' ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <ClipboardList className="h-4 w-4" />
                      )}
                      Open closure draft
                    </button>
                  </div>
                )}

                {closure && (
                  <div className="space-y-3">
                    <label className="block text-sm">
                      <span className="text-xs font-medium text-slate-500">
                        Service restored at (OCC-provided) *
                      </span>
                      <input
                        type="datetime-local"
                        value={restoredAt}
                        disabled={!editable}
                        onChange={(e) => setRestoredAt(e.target.value)}
                        className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="text-xs font-medium text-slate-500">
                        Final summary *
                      </span>
                      <textarea
                        value={finalSummary}
                        disabled={!editable}
                        onChange={(e) => setFinalSummary(e.target.value)}
                        rows={3}
                        className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="text-xs font-medium text-slate-500">
                        Timeline summary
                      </span>
                      <textarea
                        value={timelineSummary}
                        disabled={!editable}
                        onChange={(e) => setTimelineSummary(e.target.value)}
                        rows={4}
                        className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 font-mono text-xs disabled:bg-slate-50"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="text-xs font-medium text-slate-500">
                        Team investigation notes
                      </span>
                      <textarea
                        value={teamNotes}
                        disabled={!editable}
                        onChange={(e) => setTeamNotes(e.target.value)}
                        rows={2}
                        className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="text-xs font-medium text-slate-500">
                        Remediation notes
                      </span>
                      <textarea
                        value={remediationNotes}
                        disabled={!editable}
                        onChange={(e) => setRemediationNotes(e.target.value)}
                        rows={2}
                        className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                      />
                    </label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="block text-sm">
                        <span className="text-xs font-medium text-slate-500">RCA status</span>
                        <select
                          value={rcaStatus}
                          disabled={!editable}
                          onChange={(e) =>
                            setRcaStatus(e.target.value as 'unconfirmed' | 'confirmed')
                          }
                          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                        >
                          <option value="unconfirmed">Unconfirmed</option>
                          <option value="confirmed">Confirmed</option>
                        </select>
                      </label>
                      <label className="block text-sm">
                        <span className="text-xs font-medium text-slate-500">
                          RCA statement {rcaStatus === 'confirmed' ? '*' : ''}
                        </span>
                        <input
                          value={rcaStatement}
                          disabled={!editable}
                          onChange={(e) => setRcaStatement(e.target.value)}
                          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm disabled:bg-slate-50"
                        />
                      </label>
                    </div>

                    {editable && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button
                          type="button"
                          onClick={onSaveDraft}
                          disabled={!!busy}
                          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 disabled:opacity-60"
                        >
                          <Save className="h-4 w-4" />
                          Save draft
                        </button>
                        <button
                          type="button"
                          onClick={onSubmit}
                          disabled={!!busy}
                          className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                        >
                          <Send className="h-4 w-4" />
                          Submit for OCC approval
                        </button>
                      </div>
                    )}

                    {pending && (
                      <div className="space-y-3 border-t border-slate-100 pt-3">
                        <p className="text-sm text-amber-800">
                          Awaiting OCC approval. AI cannot resolve ServiceNow or PagerDuty
                          without this step.
                        </p>
                        <label className="block text-sm">
                          <span className="text-xs font-medium text-slate-500">
                            Rejection reason (if rejecting)
                          </span>
                          <input
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                          />
                        </label>
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={onApprove}
                            disabled={!!busy}
                            className="inline-flex items-center gap-2 rounded-md bg-emerald-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                            OCC approve &amp; sync SN/PD
                          </button>
                          <button
                            type="button"
                            onClick={onReject}
                            disabled={!!busy}
                            className="inline-flex items-center gap-2 rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-60"
                          >
                            <XCircle className="h-4 w-4" />
                            Reject
                          </button>
                        </div>
                      </div>
                    )}

                    {closure.status === 'completed' && (
                      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
                        Closure completed by {closure.approved_by}. SN resolve mock=
                        {String(closure.servicenow_resolve_mock)}; PD resolve mock=
                        {String(closure.pagerduty_resolve_mock)}.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

function MetricList({
  title,
  rows,
}: {
  title: string
  rows: [string, number][]
}) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">{title}</h3>
      <ul className="space-y-1 text-sm">
        {rows.slice(0, 6).map(([label, count]) => (
          <li key={label} className="flex justify-between gap-2">
            <span className="truncate text-slate-700">{label}</span>
            <span className="font-medium text-slate-900">{count}</span>
          </li>
        ))}
        {rows.length === 0 && <li className="text-slate-400">No data yet</li>}
      </ul>
    </div>
  )
}
