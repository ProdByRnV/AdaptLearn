import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { fetchCurrentUser, loginRequest, registerRequest } from '@/api/auth'
import { getErrorMessage, setUnauthorizedHandler, tokenStorage } from '@/api/client'
import { AuthContext } from '@/context/auth-context'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => tokenStorage.get())
  const [user, setUser] = useState(null)
  // With a stored token, the session is unknown until /auth/me answers.
  const [loading, setLoading] = useState(() => tokenStorage.get() !== null)
  const [bootError, setBootError] = useState(null)
  const [sessionExpired, setSessionExpired] = useState(false)

  // Bumped whenever the session changes, so a /auth/me answer for an older session is ignored.
  const generation = useRef(0)

  const clearSession = useCallback(() => {
    generation.current += 1
    tokenStorage.clear()
    setToken(null)
    setUser(null)
    setBootError(null)
    setLoading(false)
  }, [])

  // Ask the server who the stored token belongs to. State only changes once it answers.
  const loadUser = useCallback(async () => {
    const current = ++generation.current
    try {
      const me = await fetchCurrentUser()
      if (current === generation.current) setUser(me)
    } catch (error) {
      if (current !== generation.current) return
      if (error.response?.status === 401) {
        clearSession()
      } else {
        // The token may still be valid (e.g. the server is down), so keep it and offer a retry.
        setBootError(getErrorMessage(error))
      }
    } finally {
      if (current === generation.current) setLoading(false)
    }
  }, [clearSession])

  const refreshUser = useCallback(async () => {
    if (!tokenStorage.get()) {
      clearSession()
      return
    }
    setLoading(true)
    setBootError(null)
    await loadUser()
  }, [clearSession, loadUser])

  const startSession = useCallback((data) => {
    generation.current += 1
    tokenStorage.set(data.access_token)
    setToken(data.access_token)
    setUser(data.user)
    setSessionExpired(false)
    setBootError(null)
    setLoading(false)
    return data.user
  }, [])

  const login = useCallback(async (fields) => startSession(await loginRequest(fields)), [startSession])
  const register = useCallback(async (fields) => startSession(await registerRequest(fields)), [startSession])

  const logout = useCallback(() => {
    setSessionExpired(false)
    clearSession()
  }, [clearSession])

  // Restore the session from a stored token on first load (loading already starts as true).
  // loadUser only sets state after /auth/me answers, which the lint rule can't see through the await.
  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    if (tokenStorage.get()) loadUser()
  }, [loadUser])

  // Any API call rejected with 401 for the current token ends the session.
  useEffect(
    () =>
      setUnauthorizedHandler(() => {
        setSessionExpired(true)
        clearSession()
      }),
    [clearSession],
  )

  // Keep tabs in step: logging out (or in as someone else) in one tab applies to all of them.
  useEffect(() => {
    function onStorage(event) {
      if (event.key !== null && event.key !== tokenStorage.key) return
      const next = tokenStorage.get()
      if (!next) {
        setSessionExpired(false)
        clearSession()
      } else if (event.key === null || event.newValue !== event.oldValue) {
        setToken(next)
        setUser(null)
        refreshUser()
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [clearSession, refreshUser])

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(token && user),
      sessionExpired,
      bootError,
      register,
      login,
      logout,
      refreshUser,
    }),
    [user, token, loading, sessionExpired, bootError, register, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
