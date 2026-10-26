import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageLoader } from '@/components/common/Loader'
import { useAuth } from '@/hooks/useAuth'
import { redirectTarget } from '@/lib/redirect'

/** Login and register: a signed-in learner is sent on to where they were going, or the dashboard. */
export function PublicOnlyRoute() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader label="Checking your session…" />
  if (isAuthenticated) return <Navigate to={redirectTarget(location.state?.from)} replace />
  return <Outlet />
}
