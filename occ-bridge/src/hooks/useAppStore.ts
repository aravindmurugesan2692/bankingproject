import { useSyncExternalStore } from 'react'
import { getSnapshot, subscribe } from '../api/bridgeApi'

export function useAppStore() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
}

export function useOperator() {
  return useAppStore().operator
}

export function useActiveSession() {
  return useAppStore().active
}

export function useBridgeHistory() {
  return useAppStore().history
}

export function useBridges() {
  return useAppStore().bridges
}
