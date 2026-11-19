export function MockBadge({ label = 'MOCK DATA' }: { label?: string }) {
  return (
    <span className="inline-flex items-center rounded border border-amber-300/80 bg-amber-50 px-2 py-0.5 font-mono text-[10px] font-medium tracking-wide text-amber-800 uppercase">
      {label}
    </span>
  )
}
