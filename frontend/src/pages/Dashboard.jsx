import { LayoutDashboard } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/hooks/useAuth'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <>
      <PageHeader title={`Welcome back, ${user.username}`} description="Your progress at a glance." />
      <EmptyState
        icon={LayoutDashboard}
        title="Dashboard coming next"
        description="Stats, recommended topics, topics that need attention, recent attempts and mastery bars are built in Phase 16."
      />
    </>
  )
}
