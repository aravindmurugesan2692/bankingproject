import { Construction } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { NAV_ITEMS } from '../nav'
import { MockBadge } from '../components/MockBadge'

export function ComingSoonPage() {
  const location = useLocation()
  const item = NAV_ITEMS.find((nav) => nav.path === location.pathname)

  return (
    <div className="mx-auto max-w-2xl animate-fade-up rounded-xl border border-[var(--color-slate-line)] bg-white/90 p-8 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--color-accent-soft)] text-[var(--color-accent)]">
          <Construction className="h-6 w-6" />
        </div>
        <MockBadge label="PHASE SHELL" />
      </div>
      <h2 className="mt-5 text-2xl font-bold tracking-tight text-[var(--color-ink)]">
        {item?.label ?? 'Feature'} — coming in a later phase
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">
        Phase 1 delivers the dashboard, FastAPI/SQLite backend, and incident initiation only. This
        page is a navigation shell so the enterprise IA is visible now; functionality lands after
        Phase 1 approval.
      </p>
    </div>
  )
}
