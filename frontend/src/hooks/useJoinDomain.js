import { useState } from 'react'
import { useNavigate } from 'react-router'

import { getErrorMessage } from '@/api/client'
import { joinDomain } from '@/api/domains'
import { domainPath } from '@/lib/domains'

/**
 * Join a domain, then go to its onboarding (or its dashboard, if the learner had already been
 * through it). Returns {join, joining: the domain id being joined, error: {domainId, message}}.
 */
export function useJoinDomain() {
  const navigate = useNavigate()
  const [joining, setJoining] = useState(null)
  const [error, setError] = useState(null)

  async function join(domainId) {
    if (joining) return
    setJoining(domainId)
    setError(null)
    try {
      const enrolment = await joinDomain(domainId)
      navigate(domainPath(domainId, enrolment.onboarded ? 'dashboard' : 'onboarding'))
    } catch (err) {
      setError({ domainId, message: getErrorMessage(err, "Couldn't join this domain. Please try again.") })
      setJoining(null)
    }
  }

  return { join, joining, error }
}
