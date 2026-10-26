import { Outlet, useLocation } from 'react-router'

import { FullPageLoader } from '@/components/common/Loader'
import { useAuth } from '@/hooks/useAuth'
import { PostAuthRedirect } from '@/routes/PostAuthRedirect'

/**
 * Login and register. Once the learner is signed in (already, or by submitting the form), this
 * guard moves them on, so the forms never navigate themselves and can't race it.
 */
export function PublicOnlyRoute() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader label="Checking your session…" />
  if (isAuthenticated) return <PostAuthRedirect from={location.state?.from} />
  return <Outlet />
}
