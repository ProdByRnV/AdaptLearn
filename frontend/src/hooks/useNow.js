import { useEffect, useState } from 'react'

/** The current time in ms, refreshed every `intervalMs` while `enabled` (for countdowns). */
export function useNow(enabled = true, intervalMs = 250) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!enabled) return undefined
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [enabled, intervalMs])

  return now
}
