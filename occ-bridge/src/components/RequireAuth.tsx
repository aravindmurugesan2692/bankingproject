import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useOperator } from '../hooks/useAppStore'

export function RequireAuth({ children }: { children: ReactNode }) {
  const operator = useOperator()
  const location = useLocation()

  if (!operator) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}
