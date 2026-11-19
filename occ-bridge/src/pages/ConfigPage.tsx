import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  getSnapshot,
  resetBridgeUrls,
  updateBridgeUrl,
} from '../api/bridgeApi'
import { DEFAULT_BRIDGES } from '../config/defaults'
import type { BridgeId } from '../types'

export function ConfigPage() {
  const [urls, setUrls] = useState<Record<BridgeId, string>>(() => {
    const bridges = getSnapshot().bridges
    return Object.fromEntries(
      bridges.map((b) => [b.id, b.teamsMeetingUrl]),
    ) as Record<BridgeId, string>
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const bridges = getSnapshot().bridges
    setUrls(
      Object.fromEntries(
        bridges.map((b) => [b.id, b.teamsMeetingUrl]),
      ) as Record<BridgeId, string>,
    )
  }, [])

  function onSave(e: FormEvent) {
    e.preventDefault()
    ;(Object.keys(urls) as BridgeId[]).forEach((id) => {
      updateBridgeUrl(id, urls[id])
    })
    setSaved(true)
    window.setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Config</h1>
          <p className="lede">
            Placeholder Teams meeting links for STS1–STS4. Persist locally until
            real URLs are provided. Live ServiceNow / PagerDuty / Azure Bot
            remain mocked.
          </p>
        </div>
      </header>

      <form className="panel config-form" onSubmit={onSave}>
        <header className="panel__header">
          <h2>Teams meeting links</h2>
          <p>Editable placeholders — SAMPLE only.</p>
        </header>

        <div className="config-fields">
          {(Object.keys(urls) as BridgeId[]).map((id) => (
            <label key={id} htmlFor={`url-${id}`}>
              {id}
              <input
                id={`url-${id}`}
                type="url"
                value={urls[id]}
                onChange={(e) =>
                  setUrls((prev) => ({ ...prev, [id]: e.target.value }))
                }
              />
            </label>
          ))}
        </div>

        <div className="header-actions">
          <button type="submit">Save links</button>
          <button
            type="button"
            className="ghost"
            onClick={() => {
              resetBridgeUrls()
              setUrls(
                Object.fromEntries(
                  DEFAULT_BRIDGES.map((b) => [b.id, b.teamsMeetingUrl]),
                ) as Record<BridgeId, string>,
              )
              setSaved(true)
              window.setTimeout(() => setSaved(false), 2000)
            }}
          >
            Reset defaults
          </button>
          {saved ? <span className="ok-text">Saved</span> : null}
        </div>
      </form>

      <section className="panel">
        <header className="panel__header">
          <h2>Integration swap points</h2>
          <p>Replace these modules when management approves live APIs.</p>
        </header>
        <ul className="swap-list">
          <li>
            <code>src/integrations/servicenow.ts</code> — createIncident
          </li>
          <li>
            <code>src/integrations/pagerduty.ts</code> — pageTeam
          </li>
          <li>
            <code>src/integrations/teams.ts</code> — meeting links + Azure Bot
          </li>
          <li>
            <code>src/ai/recommend.ts</code> — triage / LLM
          </li>
          <li>
            <code>src/api/bridgeApi.ts</code> — shared console/bot API façade
          </li>
        </ul>
      </section>
    </div>
  )
}
