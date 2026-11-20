import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type DemoRole = 'occ_engineer' | 'occ_administrator' | 'viewer'

const USER_KEY = 'occ_demo_user'
const ROLE_KEY = 'occ_demo_role'

type AuthState = {
  displayName: string
  role: DemoRole
  setIdentity: (displayName: string, role: DemoRole) => void
  headers: Record<string, string>
}

const AuthContext = createContext<AuthState | null>(null)

function loadRole(): DemoRole {
  const raw = localStorage.getItem(ROLE_KEY) || 'occ_engineer'
  if (raw === 'occ_administrator' || raw === 'viewer' || raw === 'occ_engineer') {
    return raw
  }
  return 'occ_engineer'
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [displayName, setDisplayName] = useState(
    () => localStorage.getItem(USER_KEY) || 'OCC Engineer · Demo User',
  )
  const [role, setRole] = useState<DemoRole>(loadRole)

  const setIdentity = useCallback((name: string, nextRole: DemoRole) => {
    localStorage.setItem(USER_KEY, name)
    localStorage.setItem(ROLE_KEY, nextRole)
    setDisplayName(name)
    setRole(nextRole)
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      displayName,
      role,
      setIdentity,
      headers: {
        'X-OCC-User': displayName,
        'X-OCC-Role': role,
      },
    }),
    [displayName, role, setIdentity],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}

export function roleLabel(role: DemoRole): string {
  if (role === 'occ_administrator') return 'OCC Administrator'
  if (role === 'viewer') return 'Viewer (read-only)'
  return 'OCC Engineer'
}
