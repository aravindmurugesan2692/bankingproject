import { NavLink, Outlet } from 'react-router-dom'
import { signOut } from '../../api/bridgeApi'
import { useActiveSession, useOperator } from '../../hooks/useAppStore'
import { SampleBanner } from '../SampleBanner'

export function AppShell() {
  const operator = useOperator()
  const active = useActiveSession()

  return (
    <div className="app-root">
      <SampleBanner />
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__eyebrow">Operation Center</span>
          <strong>OCC Bridge Assist</strong>
        </div>
        <nav className="topbar__nav" aria-label="Primary">
          <NavLink to="/" end>
            Bridges
          </NavLink>
          <NavLink to="/workspace" className={active ? undefined : 'is-muted'}>
            Workspace
            {active ? <span className="nav-badge">{active.bridgeId}</span> : null}
          </NavLink>
          <NavLink to="/bot">Teams bot</NavLink>
          <NavLink to="/history">History</NavLink>
          <NavLink to="/config">Config</NavLink>
        </nav>
        <div className="topbar__user">
          <span className="operator-chip">{operator?.name ?? 'OCC'}</span>
          <button type="button" className="ghost compact" onClick={() => signOut()}>
            Sign out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
