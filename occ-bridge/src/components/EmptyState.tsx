import type { ReactNode } from 'react'

interface Props {
  title: string
  body: string
  action?: ReactNode
}

export function EmptyState({ title, body, action }: Props) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>{body}</p>
      {action}
    </div>
  )
}
