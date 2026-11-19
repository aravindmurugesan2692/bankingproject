const STYLES: Record<string, string> = {
  New: 'bg-sky-50 text-sky-800 border-sky-200',
  Analyzed: 'bg-cyan-50 text-cyan-800 border-cyan-200',
  Active: 'bg-teal-50 text-teal-800 border-teal-200',
  'Pending Approval': 'bg-violet-50 text-violet-800 border-violet-200',
  Resolved: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  Closed: 'bg-slate-100 text-slate-600 border-slate-200',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${STYLES[status] ?? 'bg-slate-50 text-slate-600 border-slate-200'}`}
    >
      {status}
    </span>
  )
}
