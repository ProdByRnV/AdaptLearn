import { ClipboardCheck } from 'lucide-react'
import { useParams } from 'react-router'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

export default function QuizPage() {
  const { topicId } = useParams()

  return (
    <>
      <PageHeader title="Quiz" description={`Topic: ${topicId}`} />
      <EmptyState
        icon={ClipboardCheck}
        title="Quiz screen coming soon"
        description="The proctored, one-question-at-a-time quiz is built in Phase 17."
      />
    </>
  )
}
