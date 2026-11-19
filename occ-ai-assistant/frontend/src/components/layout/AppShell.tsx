import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { NAV_ITEMS } from '../../nav'
import { MockBadge } from '../MockBadge'

export function AppShell() {
  const [open, setOpen] = useState(false)

  return (
    <div className="app-shell-bg flex min-h-screen">
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-[var(--color-navy-900)] text-slate-100 shadow-xl transition-transform lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="border-b border-white/10 px-5 py-5">
          <p className="font-mono text-[10px] tracking-[0.2em] text-teal-300/90 uppercase">
            Operations Control Center
          </p>
          <h1 className="mt-1 text-xl font-bold tracking-tight text-white">OCC AI Assistant</h1>
          <p className="mt-2 text-xs text-slate-400">Phase 4 · PagerDuty</p>
          <div className="mt-3">
            <MockBadge label="MOCK MODE" />
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition ${
                    isActive
                      ? 'bg-teal-500/15 text-white ring-1 ring-teal-400/30'
                      : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0 opacity-80" />
                <span className="flex-1 leading-snug">{item.label}</span>
                {!item.phaseReady && (
                  <span className="rounded bg-white/10 px-1.5 py-0.5 text-[9px] tracking-wide text-slate-400 uppercase">
                    Later
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>
      </aside>

      {open && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          aria-label="Close menu"
          onClick={() => setOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-[var(--color-slate-line)] bg-white/85 px-4 py-3 backdrop-blur md:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-md border border-[var(--color-slate-line)] p-2 text-[var(--color-ink)] lg:hidden"
              onClick={() => setOpen((v) => !v)}
              aria-label="Toggle navigation"
            >
              {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
            <div>
              <p className="text-xs text-[var(--color-muted)]">Signed in as</p>
              <p className="text-sm font-semibold text-[var(--color-ink)]">OCC Engineer · Demo User</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-[var(--color-muted)]">
            <span className="hidden items-center gap-1.5 sm:inline-flex">
              <span className="live-dot h-2 w-2 rounded-full bg-teal-600" />
              API connected
            </span>
            <MockBadge />
          </div>
        </header>

        <main className="flex-1 px-4 py-5 md:px-6 md:py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
