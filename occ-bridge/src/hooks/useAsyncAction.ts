import { useState } from 'react'

export function useAsyncAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
    setBusy(true)
    setError(null)
    try {
      return await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
      return undefined
    } finally {
      setBusy(false)
    }
  }

  function clearError() {
    setError(null)
  }

  return { busy, error, run, clearError, setError }
}
