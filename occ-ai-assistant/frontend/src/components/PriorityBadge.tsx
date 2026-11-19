const STYLES: Record<string, string> = {
  Critical: 'bg-red-50 text-[var(--color-critical)] border-red-200',
  High: 'bg-orange-50 text-[var(--color-high)] border-orange-200',
  Medium: 'bg-amber-50 text-[var(--color-medium)] border-amber-200',
  Low: 'bg-emerald-50 text-[var(--color-low)] border-emerald-200',
}

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`inline-flex rounded border px-2 py-0.5 text-xs font-semibold ${STYLES[priority] ?? 'bg-slate-50 text-slate-600 border-slate-200'}`}
    >
      {priority}
    </span>
  )
}
