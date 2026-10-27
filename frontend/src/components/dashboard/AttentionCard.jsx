import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router'

import { ResourceList } from '@/components/topics/ResourceList'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPercent } from '@/lib/format'

/**
 * A topic the learner keeps struggling with (PRD 6.3: more than 2 attempts and mastery under 50%).
 * Resources come first, before encouraging another attempt.
 */
export function AttentionCard({ topic }) {
  return (
    <Card className="gap-4 border border-status-in-progress/60 px-5 py-5">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-status-in-progress/20 text-ink">
          <AlertTriangle aria-hidden="true" className="size-4" />
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-ink">{topic.name}</h3>
          <p className="text-sm text-body">
            {formatPercent(topic.mastery)} mastery after {topic.attempts} {topic.attempts === 1 ? 'attempt' : 'attempts'}
          </p>
        </div>
      </div>
      {topic.resources.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-ink">Review these before trying again:</p>
          <ResourceList resources={topic.resources} />
        </div>
      )}
      <Button asChild variant="outline" className="mt-auto h-9 w-full">
        <Link to={`/quiz/${encodeURIComponent(topic.id)}`} aria-label={`Retry quiz: ${topic.name}`}>
          Retry quiz
        </Link>
      </Button>
    </Card>
  )
}
