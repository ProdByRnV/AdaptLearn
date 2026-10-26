import { useCallback, useEffect, useState } from 'react'

/**
 * Load data for a page: {data, error, loading, reload}. `loader` must be stable (a module-level
 * API function). A response that arrives after the page has gone away is ignored.
 */
export function useApiData(loader) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    loader()
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch((error) => !cancelled && setState({ data: null, error, loading: false }))
    return () => {
      cancelled = true
    }
  }, [loader, attempt])

  const reload = useCallback(() => {
    setState((current) => ({ ...current, error: null, loading: true }))
    setAttempt((n) => n + 1)
  }, [])

  return { ...state, reload }
}
