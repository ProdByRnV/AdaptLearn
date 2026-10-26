import { ListChecks } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

export default function Onboarding() {
  return (
    <>
      <PageHeader title="What do you already know?" description="Pick the topics you're comfortable with so we can skip them." />
      <EmptyState
        icon={ListChecks}
        title="Onboarding coming soon"
        description="The known-topic picker is built in Phase 15."
      />
    </>
  )
}
