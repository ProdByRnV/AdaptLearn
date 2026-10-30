import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'

import { fetchHome } from '@/api/domains'
import { FullPageLoader } from '@/components/common/Loader'
import { rememberedTarget } from '@/lib/redirect'

/**
 * Where a signed-in learner lands: back to the page they were sent away from, otherwise the
 * catalogue until they have joined a domain (US-01: new accounts start by choosing what to learn,
 * then onboarding), and their home page after that.
 */
export function PostAuthRedirect({ from }) {
  const target = rememberedTarget(from)
  const [landing, setLanding] = useState(null)

  useEffect(() => {
    if (target) return undefined
    let cancelled = false
    fetchHome()
      .then((home) => !cancelled && setLanding(home.domains.length > 0 ? '/home' : '/domains'))
      // The home page shows its own error state if the API is having trouble.
      .catch(() => !cancelled && setLanding('/home'))
    return () => {
      cancelled = true
    }
  }, [target])

  const destination = target ?? landing
  if (!destination) return <FullPageLoader label="Getting things ready…" />
  return <Navigate to={destination} replace />
}
