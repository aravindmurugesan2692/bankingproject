import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { signIn } from '../api/bridgeApi'
import { SampleBanner } from '../components/SampleBanner'
import { useOperator } from '../hooks/useAppStore'

export function LoginPage() {
  const operator = useOperator()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (operator) {
    return <Navigate to="/" replace />
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    try {
      signIn(name)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed')
    }
  }

  return (
    <div className="login-page">
      <SampleBanner />
      <div className="login-card panel">
        <p className="eyebrow">Operation Center</p>
        <h1>OCC Bridge Assist</h1>
        <p className="lede">
          OCC operators only. Sign in with your operator name to manage STS
          bridges. Integrations are mocked until live APIs are approved.
        </p>
        <form className="intake-form" onSubmit={onSubmit}>
          <label htmlFor="operator">
            Operator name
            <input
              id="operator"
              type="text"
              autoComplete="name"
              placeholder="e.g. Jordan Chen"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          {error ? (
            <p className="field-error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" disabled={!name.trim()}>
            Enter console
          </button>
        </form>
      </div>
    </div>
  )
}
