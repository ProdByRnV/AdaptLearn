import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageError } from '@/components/common/ErrorState'
import { FullPageLoader } from '@/components/common/Loader'
import { useAuth } from '@/hooks/useAuth'

/** Renders child routes for a signed-in learner; otherwise sends them to /login and remembers where they were going. */
export function ProtectedRoute() {
  const { isAuthenticated, loading, bootError, refreshUser } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader label="Checking your session…" />
  if (bootError) {
    return <FullPageError title="Couldn't restore your session" message={bootError} onRetry={refreshUser} />
  }
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}
