import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageError } from '@/components/common/ErrorState'
import { FullPageLoader } from '@/components/common/Loader'
import { useAuth } from '@/hooks/useAuth'

/**
 * Renders child routes for a signed-in learner. Otherwise sends them to /login, remembering where
 * they were going, unless they just logged out on purpose (the next login starts fresh).
 */
export function ProtectedRoute() {
  const { isAuthenticated, loading, bootError, refreshUser, loggedOut } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader label="Checking your session…" />
  if (bootError) {
    return <FullPageError title="Couldn't restore your session" message={bootError} onRetry={refreshUser} />
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={loggedOut ? undefined : { from: location }} />
  }
  return <Outlet />
}
