import { CheckCircle2, LayoutDashboard } from 'lucide-react'
import { useLocation } from 'react-router'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useAuth } from '@/hooks/useAuth'
import { listNames } from '@/lib/topics'

export default function Dashboard() {
  const { user } = useAuth()
  const onboarding = useLocation().state?.onboarding

  return (
    <>
      <PageHeader title={`Welcome back, ${user.username}`} description="Your progress at a glance." />
      {onboarding && <OnboardingDone {...onboarding} />}
      <EmptyState
        icon={LayoutDashboard}
        title="Dashboard coming next"
        description="Stats, recommended topics, topics that need attention, recent attempts and mastery bars are built in Phase 16."
      />
    </>
  )
}

/** Confirmation after onboarding (US-04: the learner is sent to the dashboard). */
function OnboardingDone({ knownCount, addedPrerequisites = [] }) {
  return (
    <Alert role="status" className="mb-6 border-primary/30 bg-accent/40">
      <CheckCircle2 aria-hidden="true" className="text-primary" />
      <AlertTitle className="text-ink">You're all set</AlertTitle>
      <AlertDescription className="text-body">
        {knownCount === 0
          ? "You're starting from the beginning. Your first topics are ready."
          : `${knownCount} ${knownCount === 1 ? 'topic is' : 'topics are'} marked as known, so your path starts after them.`}
        {addedPrerequisites.length > 0 &&
          ` Their prerequisites were included too (${listNames(addedPrerequisites, 3)}).`}
      </AlertDescription>
    </Alert>
  )
}
