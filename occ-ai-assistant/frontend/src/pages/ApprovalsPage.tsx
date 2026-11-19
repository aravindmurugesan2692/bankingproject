import { useEffect, useMemo, useState } from 'react'
import {
  CheckCircle2,
  Loader2,
  Plus,
  Save,
  ShieldAlert,
  X,
  XCircle,
} from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  approveIncident,
  getApproval,
  listApprovals,
  listTeams,
  rejectIncident,
  updateApprovalDraft,
} from '../api/client'
import type { ApprovalPacket, SeverityCode, SupportTeam } from '../types'
import { MockBadge } from '../components/MockBadge'

const SEVERITIES: SeverityCode[] = ['P1', 'P2', 'P3', 'P4']
const ACTOR = 'OCC Engineer · Demo User'

export function ApprovalsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [queue, setQueue] = useState<ApprovalPacket[]>([])
  const [packet, setPacket] = useState<ApprovalPacket | null>(null)
  const [allTeams, setAllTeams] = useState<SupportTeam[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  const [severity, setSeverity] = useState<SeverityCode>('P3')
  const [description, setDescription] = useState('')
  const [teamSlugs, setTeamSlugs] = useState<string[]>([])

  const selectedId = useMemo(() => {
    const q = searchParams.get('incident')
    if (q) return Number(q)
    return queue[0]?.incident.id ?? null
  }, [searchParams, queue])

  async function refreshQueue() {
    const rows = await listApprovals()
    setQueue(rows)
    return rows
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [rows, teams] = await Promise.all([listApprovals(), listTeams()])
        if (!cancelled) {
          setQueue(rows)
          setAllTeams(teams.filter((t) => t.active))
        }
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
    if (!selectedId) {
      setPacket(null)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const detail = await getApproval(selectedId)
        if (cancelled) return
        setPacket(detail)
        setSeverity((detail.incident.working_severity as SeverityCode) || 'P3')
        setDescription(detail.incident.working_description || detail.incident.description)
        setTeamSlugs(detail.incident.selected_team_slugs || [])
        setRejectReason('')
        setSuccess(null)
        setError(null)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load packet')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  function toggleTeam(slug: string) {
    setTeamSlugs((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug],
    )
  }

  async function onSaveDraft() {
    if (!selectedId) return
    setSaving(true)
    setError(null)
    try {
      const updated = await updateApprovalDraft(selectedId, {
        working_severity: severity,
        working_description: description,
        selected_team_slugs: teamSlugs,
        actor: ACTOR,
      })
      setPacket(updated)
      await refreshQueue()
      setSuccess('Draft saved (severity / description / teams).')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function onApprove() {
    if (!selectedId) return
    setBusy(true)
    setError(null)
    try {
      const result = await approveIncident(selectedId, {
        actor: ACTOR,
        working_severity: severity,
        working_description: description,
        selected_team_slugs: teamSlugs,
      })
      const pdCount = result.pagerduty_notifications?.length ?? 0
      setSuccess(
        `Approved. ServiceNow ${result.servicenow_number}` +
          (result.servicenow_is_mock ? ' (MOCK)' : '') +
          (result.servicenow_duplicate ? ' — duplicate prevented' : '') +
          (pdCount ? ` · PagerDuty pages: ${pdCount}` : ''),
      )
      await refreshQueue()
      // After approval it leaves the queue — clear selection if gone
      const still = (await listApprovals()).find((p) => p.incident.id === selectedId)
      if (still) {
        setPacket(still)
      } else {
        setPacket(null)
        setSearchParams({})
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve failed')
    } finally {
      setBusy(false)
    }
  }

  async function onReject() {
    if (!selectedId) return
    if (!rejectReason.trim()) {
      setError('Rejection reason is required')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await rejectIncident(selectedId, {
        actor: ACTOR,
        rejection_reason: rejectReason.trim(),
      })
      setSuccess('Incident rejected — no ServiceNow record created.')
      await refreshQueue()
      setPacket(null)
      setSearchParams({})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reject failed')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading approval queue…
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Incident Approvals
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            OCC reviews AI hypotheses, adjusts severity/teams/description, then explicitly
            approves. ServiceNow is created only after Approve — never before.
          </p>
        </div>
        <MockBadge label="PHASE 4" />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-950">
          <div className="flex gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {success}
          </div>
        </div>
      )}

      {!queue.length ? (
        <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-8 text-sm text-[var(--color-muted)] shadow-sm">
          <p className="font-medium text-[var(--color-ink)]">Approval queue is empty</p>
          <p className="mt-2">
            <Link className="font-medium text-teal-800 underline" to="/initiate">
              Initiate an incident
            </Link>{' '}
            to generate analysis and enqueue it for OCC approval.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[260px_1fr]">
          <aside className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 shadow-sm">
            <div className="border-b border-[var(--color-slate-line)] px-4 py-3 text-sm font-semibold">
              Pending ({queue.length})
            </div>
            <ul className="max-h-[75vh] divide-y divide-[var(--color-slate-line)] overflow-y-auto">
              {queue.map((row) => (
                <li key={row.incident.id}>
                  <button
                    type="button"
                    onClick={() => setSearchParams({ incident: String(row.incident.id) })}
                    className={`w-full px-4 py-3 text-left text-sm ${
                      row.incident.id === selectedId ? 'bg-teal-50' : 'hover:bg-slate-50'
                    }`}
                  >
                    <p className="font-mono text-xs text-[var(--color-muted)]">
                      {row.incident.occ_incident_id}
                    </p>
                    <p className="mt-1 line-clamp-2 font-medium">{row.incident.title}</p>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">
                      {row.incident.working_severity || '—'} ·{' '}
                      {(row.incident.selected_team_slugs || []).length} teams
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          {packet && (
            <div className="space-y-4">
              <section className="rounded-xl border border-amber-200 bg-amber-50/90 p-4 text-sm text-amber-950">
                AI recommendations are hypotheses for OCC review — not confirmed root cause. External
                ServiceNow create runs only after you click Approve.
              </section>

              <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-[var(--color-muted)]">
                      {packet.incident.occ_incident_id}
                    </p>
                    <h3 className="mt-1 text-xl font-bold">{packet.incident.title}</h3>
                    <p className="mt-1 text-sm text-[var(--color-muted)]">
                      {packet.incident.application_service} · {packet.incident.environment} ·{' '}
                      {packet.incident.users_affected} users
                    </p>
                  </div>
                  <Link
                    to={`/analysis?incident=${packet.incident.id}`}
                    className="text-sm font-medium text-teal-800 underline"
                  >
                    Open analysis
                  </Link>
                </div>

                {packet.analysis && (
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <InfoBlock label="AI summary" value={packet.analysis.summary} />
                    <InfoBlock
                      label="AI suggested severity"
                      value={`${packet.analysis.suggested_priority} · ${packet.analysis.category}`}
                    />
                  </div>
                )}
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-3 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                  <h4 className="text-sm font-semibold">Modify severity</h4>
                  <div className="flex flex-wrap gap-2">
                    {SEVERITIES.map((code) => (
                      <button
                        key={code}
                        type="button"
                        onClick={() => setSeverity(code)}
                        className={`rounded-md border px-3 py-1.5 text-sm font-semibold ${
                          severity === code
                            ? 'border-teal-600 bg-teal-50 text-teal-900'
                            : 'border-[var(--color-slate-line)] bg-white'
                        }`}
                      >
                        {code}
                      </button>
                    ))}
                  </div>

                  <h4 className="pt-2 text-sm font-semibold">Edit description</h4>
                  <textarea
                    className="min-h-[120px] w-full rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />

                  <button
                    type="button"
                    onClick={onSaveDraft}
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-md border border-[var(--color-slate-line)] bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Save draft
                  </button>
                </div>

                <div className="space-y-3 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                  <h4 className="text-sm font-semibold">Add / remove support teams</h4>
                  <ul className="max-h-64 space-y-2 overflow-y-auto">
                    {allTeams.map((team) => {
                      const on = teamSlugs.includes(team.slug)
                      return (
                        <li key={team.slug}>
                          <button
                            type="button"
                            onClick={() => toggleTeam(team.slug)}
                            className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm ${
                              on
                                ? 'border-teal-300 bg-teal-50'
                                : 'border-[var(--color-slate-line)] bg-white'
                            }`}
                          >
                            <span>
                              <span className="font-medium">{team.name}</span>
                              <span className="mt-0.5 block font-mono text-[10px] text-[var(--color-muted)]">
                                {team.pagerduty_service_id}
                              </span>
                            </span>
                            {on ? (
                              <X className="h-4 w-4 text-teal-800" />
                            ) : (
                              <Plus className="h-4 w-4 text-[var(--color-muted)]" />
                            )}
                          </button>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                  <h4 className="text-sm font-semibold">PagerDuty targets (paged on approve)</h4>
                  <ul className="mt-3 space-y-2 text-sm">
                    {packet.pagerduty_placeholders.map((pd) => (
                      <li key={pd.slug} className="rounded border border-[var(--color-slate-line)] px-3 py-2">
                        <p className="font-medium">{pd.team}</p>
                        <p className="font-mono text-[10px] text-[var(--color-muted)]">
                          svc {pd.service_id} · esc {pd.escalation_policy_id}
                        </p>
                      </li>
                    ))}
                    {!packet.pagerduty_placeholders.length && (
                      <li className="text-[var(--color-muted)]">No teams selected</li>
                    )}
                  </ul>
                  <p className="mt-2 text-xs text-[var(--color-muted)]">
                    Approve creates ServiceNow then pages these teams (MOCK by default). Never pages
                    without OCC approval.
                  </p>
                </div>

                <div className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-sm font-semibold">ServiceNow create preview</h4>
                    <MockBadge />
                  </div>
                  <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-950 p-3 font-mono text-[11px] text-slate-100">
                    {JSON.stringify(packet.servicenow_preview, null, 2)}
                  </pre>
                </div>
              </section>

              <section className="rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                <h4 className="text-sm font-semibold">Audit trail</h4>
                <ul className="mt-3 max-h-48 space-y-2 overflow-y-auto text-sm">
                  {packet.audit_trail.length === 0 && (
                    <li className="text-[var(--color-muted)]">No approval actions yet</li>
                  )}
                  {packet.audit_trail.map((event) => (
                    <li key={event.id} className="border-b border-[var(--color-slate-line)] pb-2">
                      <p className="font-medium">
                        {event.action} · {event.actor}
                      </p>
                      <p className="text-xs text-[var(--color-muted)]">{event.detail}</p>
                      <p className="font-mono text-[10px] text-[var(--color-muted)]">
                        {event.created_at}
                        {event.severity ? ` · ${event.severity}` : ''}
                        {event.approved_teams?.length
                          ? ` · teams: ${event.approved_teams.join(', ')}`
                          : ''}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="flex flex-wrap items-end gap-3 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-4 shadow-sm">
                <button
                  type="button"
                  disabled={busy}
                  onClick={onApprove}
                  className="inline-flex items-center gap-2 rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-60"
                >
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  Approve + create ServiceNow
                </button>
                <div className="flex min-w-[240px] flex-1 flex-col gap-2">
                  <input
                    className="rounded-md border border-[var(--color-slate-line)] px-3 py-2 text-sm"
                    placeholder="Rejection reason (required to reject)"
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={onReject}
                    className="inline-flex items-center justify-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-800 hover:bg-red-100 disabled:opacity-60"
                  >
                    <XCircle className="h-4 w-4" />
                    Reject
                  </button>
                </div>
                <p className="w-full text-xs text-[var(--color-muted)]">
                  <ShieldAlert className="mr-1 inline h-3.5 w-3.5" />
                  Approving user, timestamp, and approved teams are written to the audit trail.
                </p>
              </section>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-slate-line)] bg-[var(--color-slate-panel)] p-3">
      <p className="text-[10px] font-semibold tracking-wide text-[var(--color-muted)] uppercase">
        {label}
      </p>
      <p className="mt-1 text-sm text-[var(--color-ink)]">{value}</p>
    </div>
  )
}
