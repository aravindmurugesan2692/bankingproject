import { useSyncExternalStore } from 'react'
import { getSession, subscribe } from '../store/sessionStore'
import type { BridgeSession } from '../types'

export function useSession(): BridgeSession | null {
  return useSyncExternalStore(subscribe, getSession, getSession)
}
