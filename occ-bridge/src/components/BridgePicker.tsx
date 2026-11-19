import { BRIDGES } from '../data/bridges'
import type { BridgeId } from '../types'

interface Props {
  disabled?: boolean
  onSelect: (id: BridgeId) => void
}

export function BridgePicker({ disabled, onSelect }: Props) {
  return (
    <section className="panel bridge-picker">
      <header className="panel__header">
        <h2>Open bridge</h2>
        <p>Select STS1–STS4 to start a mock incident bridge session.</p>
      </header>
      <div className="bridge-grid">
        {BRIDGES.map((bridge) => (
          <button
            key={bridge.id}
            type="button"
            className="bridge-card"
            disabled={disabled}
            onClick={() => onSelect(bridge.id)}
          >
            <span className="bridge-card__id">{bridge.id}</span>
            <span className="bridge-card__name">{bridge.name}</span>
            <span className="bridge-card__desc">{bridge.description}</span>
          </button>
        ))}
      </div>
    </section>
  )
}
