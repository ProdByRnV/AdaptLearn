import { useCallback, useEffect, useState } from 'react'

/**
 * Load data for a page: {data, error, loading, reload}. `loader` should be stable (a module-level
 * API function, or one memoised on its arguments); a different loader, such as the same page for
 * another domain, starts over from loading. A response for an old loader, or one that arrives
 * after the page has gone away, is ignored.
 */
export function useApiData(loader) {
  const [state, setState] = useState({ loader, data: null, error: null, loading: true })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    loader()
      .then((data) => !cancelled && setState({ loader, data, error: null, loading: false }))
      .catch((error) => !cancelled && setState({ loader, data: null, error, loading: false }))
    return () => {
      cancelled = true
    }
  }, [loader, attempt])

  const reload = useCallback(() => {
    setState((current) => ({ ...current, error: null, loading: true }))
    setAttempt((n) => n + 1)
  }, [])

  const { data, error, loading } = state.loader === loader ? state : { data: null, error: null, loading: true }
  return { data, error, loading, reload }
}
