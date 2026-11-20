import { useEffect, useState } from 'react'
import { Loader2, Save, Shield, ShieldAlert } from 'lucide-react'
import {
  fetchSettings,
  recordDemoIdentity,
  setApiAuthHeaders,
  updateForceMocks,
} from '../api/client'
import { roleLabel, useAuth, type DemoRole } from '../auth'
import type { SettingsStatus } from '../types'
import { MockBadge } from '../components/MockBadge'

export function SettingsPage() {
  const auth = useAuth()
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [name, setName] = useState(auth.displayName)
  const [role, setRole] = useState<DemoRole>(auth.role)
  const [forceLlm, setForceLlm] = useState(false)
  const [forceSn, setForceSn] = useState(false)
  const [forcePd, setForcePd] = useState(false)
  const [forceTeams, setForceTeams] = useState(false)

  async function refresh() {
    const s = await fetchSettings()
    setStatus(s)
    setForceLlm(!!s.force_mocks.force_mock_llm)
    setForceSn(!!s.force_mocks.force_mock_servicenow)
    setForcePd(!!s.force_mocks.force_mock_pagerduty)
    setForceTeams(!!s.force_mocks.force_mock_teams)
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

  async function onSaveIdentity(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await recordDemoIdentity({ display_name: name, role })
      auth.setIdentity(name, role)
      setApiAuthHeaders({ 'X-OCC-User': name, 'X-OCC-Role': role })
      await refresh()
      setSuccess(`Demo identity set to ${name} (${roleLabel(role)}). Headers updated.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Identity update failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveForceMocks(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const s = await updateForceMocks({
        force_mock_llm: forceLlm,
        force_mock_servicenow: forceSn,
        force_mock_pagerduty: forcePd,
        force_mock_teams: forceTeams,
        actor: auth.displayName,
      })
      setStatus(s)
      setSuccess('Force-mock flags saved (Administrator only). No secrets stored.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Force-mock update failed')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[var(--color-muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading settings…
      </div>
    )
  }

  const isAdmin = auth.role === 'occ_administrator'

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-[var(--color-navy-900)]">Settings</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Auth-ready demo identity, MOCK status, and per-integration force-mock toggles.
          API credentials stay in environment variables — never in the browser.
        </p>
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

      {status && (
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Runtime status
            </h2>
            <MockBadge label={status.data_label} />
          </div>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs text-slate-500">MOCK_MODE (env)</dt>
              <dd className="font-medium">{String(status.mock_mode)}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Auth mode</dt>
              <dd className="font-medium">{status.auth_mode}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Server sees user</dt>
              <dd className="font-medium">{status.current_user}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Server sees role</dt>
              <dd className="font-medium">{status.current_role}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-slate-500">{status.note}</p>
          <p className="mt-1 text-xs text-slate-500">
            secrets_in_frontend={String(status.secrets_in_frontend)} — always false by design.
          </p>
        </section>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          <Shield className="h-4 w-4" />
          Demo identity (RBAC headers)
        </h2>
        <form onSubmit={onSaveIdentity} className="space-y-3">
          <label className="block text-sm">
            <span className="text-xs font-medium text-slate-500">Display name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="text-xs font-medium text-slate-500">Role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as DemoRole)}
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
            >
              <option value="occ_engineer">OCC Engineer</option>
              <option value="occ_administrator">OCC Administrator</option>
              <option value="viewer">Viewer (read-only — denials)</option>
            </select>
          </label>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--color-navy-900)] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            Apply demo identity
          </button>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          <ShieldAlert className="h-4 w-4" />
          Integrations (safe status)
        </h2>
        <ul className="divide-y divide-slate-100">
          {(status?.integrations || []).map((row) => (
            <li key={row.name} className="flex flex-wrap items-start justify-between gap-2 py-3 text-sm">
              <div>
                <div className="font-medium text-[var(--color-navy-900)]">{row.name}</div>
                <div className="text-xs text-slate-500">{row.note}</div>
              </div>
              <div className="text-right text-xs text-slate-600">
                <div>configured={String(row.configured)}</div>
                <div>effectively_mock={String(row.effectively_mock)}</div>
                {row.force_mock && <MockBadge label="FORCE MOCK" />}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Force mock overrides
        </h2>
        {!isAdmin && (
          <p className="mb-3 text-sm text-amber-800">
            Switch to OCC Administrator to change force-mock flags. Engineers can view status only.
          </p>
        )}
        <form onSubmit={onSaveForceMocks} className="space-y-2">
          {[
            ['LLM', forceLlm, setForceLlm],
            ['ServiceNow', forceSn, setForceSn],
            ['PagerDuty', forcePd, setForcePd],
            ['Teams / Graph', forceTeams, setForceTeams],
          ].map(([label, value, setter]) => (
            <label key={String(label)} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={Boolean(value)}
                disabled={!isAdmin || busy}
                onChange={(e) => (setter as (v: boolean) => void)(e.target.checked)}
              />
              Force mock {String(label)} even if credentials exist
            </label>
          ))}
          <button
            type="submit"
            disabled={!isAdmin || busy}
            className="mt-2 inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            Save force-mock flags
          </button>
        </form>
      </section>
    </div>
  )
}
