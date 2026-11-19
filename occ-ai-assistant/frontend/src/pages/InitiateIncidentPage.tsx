import { useState, type FormEvent, type ReactNode } from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { createIncident } from '../api/client'
import type { Environment, Incident, IncidentAnalysis } from '../types'
import { MockBadge } from '../components/MockBadge'

type FormState = {
  title: string
  description: string
  application_service: string
  environment: Environment | ''
  business_impact: string
  users_affected: string
  issue_start_time: string
  error_messages: string
  affected_infrastructure: string
  additional_observations: string
}

const INITIAL: FormState = {
  title: '',
  description: '',
  application_service: '',
  environment: '',
  business_impact: '',
  users_affected: '',
  issue_start_time: '',
  error_messages: '',
  affected_infrastructure: '',
  additional_observations: '',
}

export function InitiateIncidentPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<FormState>(INITIAL)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [created, setCreated] = useState<Incident | null>(null)
  const [analysis, setAnalysis] = useState<IncidentAnalysis | null>(null)

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function validate(): boolean {
    const errors: Record<string, string> = {}
    if (form.title.trim().length < 3) errors.title = 'Title is required (min 3 characters)'
    if (form.description.trim().length < 10)
      errors.description = 'Description is required (min 10 characters)'
    if (!form.application_service.trim())
      errors.application_service = 'Application or service name is required'
    if (!form.environment) errors.environment = 'Environment is required'
    if (form.business_impact.trim().length < 3)
      errors.business_impact = 'Business impact is required'
    if (form.users_affected === '' || Number.isNaN(Number(form.users_affected))) {
      errors.users_affected = 'Number of users affected is required'
    } else if (Number(form.users_affected) < 0) {
      errors.users_affected = 'Must be zero or greater'
    }
    if (!form.issue_start_time) errors.issue_start_time = 'Issue start time is required'
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setApiError(null)
    setCreated(null)
    setAnalysis(null)
    if (!validate()) return

    setSubmitting(true)
    try {
      const result = await createIncident({
        title: form.title.trim(),
        description: form.description.trim(),
        application_service: form.application_service.trim(),
        environment: form.environment as Environment,
        business_impact: form.business_impact.trim(),
        users_affected: Number(form.users_affected),
        issue_start_time: new Date(form.issue_start_time).toISOString(),
        error_messages: form.error_messages.trim() || null,
        affected_infrastructure: form.affected_infrastructure.trim() || null,
        additional_observations: form.additional_observations.trim() || null,
        created_by: 'OCC Engineer · Demo User',
      })
      setCreated(result.incident)
      setAnalysis(result.analysis)
      setForm(INITIAL)
      setFieldErrors({})
      if (result.incident?.id) {
        navigate(`/analysis?incident=${result.incident.id}`)
      }
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Failed to create incident')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-ink)]">
            Initiate Incident
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Capture a user-reported issue. Mandatory fields are validated before POST to FastAPI.
          </p>
        </div>
        <MockBadge label="PHASE 2 · AUTO ANALYSIS" />
      </div>

      {created && (
        <div className="animate-fade-up rounded-xl border border-teal-200 bg-teal-50/80 p-4 text-sm text-teal-950">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-5 w-5 text-teal-700" />
            <div>
              <p className="font-semibold">Incident persisted and AI analysis started</p>
              <p className="mt-1 font-mono text-xs">
                {created.occ_incident_id} · internal id {created.id}
                {analysis ? ` · ${analysis.suggested_priority}` : ''}
              </p>
              <p className="mt-2 text-[var(--color-muted)]">
                Review structured recommendations on{' '}
                <Link
                  className="font-medium text-teal-800 underline"
                  to={`/analysis?incident=${created.id}`}
                >
                  Incident Analysis
                </Link>
                . Approvals / ServiceNow are Phase 3.
              </p>
            </div>
          </div>
        </div>
      )}

      {apiError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {apiError}
        </div>
      )}

      <form
        onSubmit={onSubmit}
        className="animate-fade-up-delay-1 space-y-4 rounded-xl border border-[var(--color-slate-line)] bg-white/95 p-5 shadow-sm md:p-6"
        noValidate
      >
        <Field
          label="Incident title"
          required
          error={fieldErrors.title}
          htmlFor="title"
        >
          <input
            id="title"
            className={inputClass(fieldErrors.title)}
            value={form.title}
            onChange={(e) => update('title', e.target.value)}
            placeholder="Short, actionable title"
          />
        </Field>

        <Field
          label="User-reported issue description"
          required
          error={fieldErrors.description}
          htmlFor="description"
        >
          <textarea
            id="description"
            rows={4}
            className={inputClass(fieldErrors.description)}
            value={form.description}
            onChange={(e) => update('description', e.target.value)}
            placeholder="What did the user report? Include symptoms and context."
          />
        </Field>

        <div className="grid gap-4 md:grid-cols-2">
          <Field
            label="Application or service name"
            required
            error={fieldErrors.application_service}
            htmlFor="application_service"
          >
            <input
              id="application_service"
              className={inputClass(fieldErrors.application_service)}
              value={form.application_service}
              onChange={(e) => update('application_service', e.target.value)}
            />
          </Field>

          <Field
            label="Environment"
            required
            error={fieldErrors.environment}
            htmlFor="environment"
          >
            <select
              id="environment"
              className={inputClass(fieldErrors.environment)}
              value={form.environment}
              onChange={(e) => update('environment', e.target.value as Environment | '')}
            >
              <option value="">Select environment</option>
              <option value="Production">Production</option>
              <option value="QA">QA</option>
              <option value="Development">Development</option>
            </select>
          </Field>
        </div>

        <Field
          label="Business impact"
          required
          error={fieldErrors.business_impact}
          htmlFor="business_impact"
        >
          <textarea
            id="business_impact"
            rows={2}
            className={inputClass(fieldErrors.business_impact)}
            value={form.business_impact}
            onChange={(e) => update('business_impact', e.target.value)}
          />
        </Field>

        <div className="grid gap-4 md:grid-cols-2">
          <Field
            label="Number of users affected"
            required
            error={fieldErrors.users_affected}
            htmlFor="users_affected"
          >
            <input
              id="users_affected"
              type="number"
              min={0}
              className={inputClass(fieldErrors.users_affected)}
              value={form.users_affected}
              onChange={(e) => update('users_affected', e.target.value)}
            />
          </Field>

          <Field
            label="Issue start time"
            required
            error={fieldErrors.issue_start_time}
            htmlFor="issue_start_time"
          >
            <input
              id="issue_start_time"
              type="datetime-local"
              className={inputClass(fieldErrors.issue_start_time)}
              value={form.issue_start_time}
              onChange={(e) => update('issue_start_time', e.target.value)}
            />
          </Field>
        </div>

        <Field label="Error messages" htmlFor="error_messages">
          <textarea
            id="error_messages"
            rows={2}
            className={inputClass()}
            value={form.error_messages}
            onChange={(e) => update('error_messages', e.target.value)}
            placeholder="Optional"
          />
        </Field>

        <Field
          label="Affected infrastructure or components, if known"
          htmlFor="affected_infrastructure"
        >
          <textarea
            id="affected_infrastructure"
            rows={2}
            className={inputClass()}
            value={form.affected_infrastructure}
            onChange={(e) => update('affected_infrastructure', e.target.value)}
            placeholder="Optional"
          />
        </Field>

        <Field label="Additional observations" htmlFor="additional_observations">
          <textarea
            id="additional_observations"
            rows={2}
            className={inputClass()}
            value={form.additional_observations}
            onChange={(e) => update('additional_observations', e.target.value)}
            placeholder="Optional"
          />
        </Field>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:opacity-60"
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {submitting ? 'Submitting…' : 'Create incident'}
          </button>
          <p className="text-xs text-[var(--color-muted)]">
            Posts to <span className="font-mono">POST /api/incidents</span>
          </p>
        </div>
      </form>
    </div>
  )
}

function inputClass(error?: string) {
  return `mt-1 w-full rounded-md border bg-white px-3 py-2 text-sm text-[var(--color-ink)] outline-none transition focus:ring-2 focus:ring-teal-600/30 ${
    error
      ? 'border-red-300 focus:border-red-400'
      : 'border-[var(--color-slate-line)] focus:border-teal-600'
  }`
}

function Field({
  label,
  required,
  error,
  htmlFor,
  children,
}: {
  label: string
  required?: boolean
  error?: string
  htmlFor: string
  children: ReactNode
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="text-sm font-medium text-[var(--color-ink)]">
        {label}
        {required && <span className="ml-1 text-red-600">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
