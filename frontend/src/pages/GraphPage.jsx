import { Network } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { TopicStatusBadge } from '@/components/topics/TopicStatusBadge'
import { TOPIC_STATUS_ORDER } from '@/lib/topic-status'

export default function GraphPage() {
  return (
    <>
      <PageHeader
        title="Knowledge graph"
        description="Every topic and the prerequisites between them."
        actions={
          <ul aria-label="Topic status legend" className="flex flex-wrap gap-2">
            {TOPIC_STATUS_ORDER.map((status) => (
              <li key={status}>
                <TopicStatusBadge status={status} />
              </li>
            ))}
          </ul>
        }
      />
      <EmptyState icon={Network} title="Graph coming soon" description="The interactive graph is built in Phase 18." />
    </>
  )
}
