import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'

import { fetchLearningPath } from '@/api/topics'
import { FullPageLoader } from '@/components/common/Loader'
import { rememberedTarget } from '@/lib/redirect'

/**
 * Where a signed-in learner lands: back to the page they were sent away from, otherwise onboarding
 * until they have done it (US-01: new accounts go to onboarding) and the dashboard after that.
 */
export function PostAuthRedirect({ from }) {
  const target = rememberedTarget(from)
  const [landing, setLanding] = useState(null)

  useEffect(() => {
    if (target) return undefined
    let cancelled = false
    fetchLearningPath()
      .then((path) => !cancelled && setLanding(path.onboarded ? '/dashboard' : '/onboarding'))
      // The dashboard shows its own error state if the API is having trouble.
      .catch(() => !cancelled && setLanding('/dashboard'))
    return () => {
      cancelled = true
    }
  }, [target])

  const destination = target ?? landing
  if (!destination) return <FullPageLoader label="Getting things ready…" />
  return <Navigate to={destination} replace />
}
