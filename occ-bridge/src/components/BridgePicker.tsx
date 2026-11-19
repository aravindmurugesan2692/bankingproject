import { useBridges } from '../hooks/useAppStore'
import type { BridgeId } from '../types'

interface Props {
  disabled?: boolean
  activeBridgeId?: BridgeId | null
  onSelect: (id: BridgeId) => void
}

export function BridgePicker({ disabled, activeBridgeId, onSelect }: Props) {
  const bridges = useBridges()

  return (
    <section className="panel bridge-picker">
      <header className="panel__header">
        <h2>Bridge home</h2>
        <p>Open STS1–STS4 to start an OCC-managed incident bridge.</p>
      </header>
      <div className="bridge-grid">
        {bridges.map((bridge) => {
          const isActive = activeBridgeId === bridge.id
          return (
            <button
              key={bridge.id}
              type="button"
              className={`bridge-card ${isActive ? 'is-active' : ''}`}
              disabled={disabled}
              onClick={() => onSelect(bridge.id)}
            >
              <span className="bridge-card__id">{bridge.id}</span>
              <span className="bridge-card__name">{bridge.name}</span>
              <span className="bridge-card__desc">{bridge.description}</span>
              {isActive ? (
                <span className="bridge-card__status">Active now</span>
              ) : null}
            </button>
          )
        })}
      </div>
    </section>
  )
}
