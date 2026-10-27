import { ArrowRight, ShieldAlert } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { Badge } from '@/components/ui/badge'
import { formatDateTime, formatPercent, timeAgo } from '@/lib/format'

/** The latest quiz attempts, newest first, with their result and whether they counted. */
export function RecentAttempts({ attempts }) {
  if (attempts.length === 0) {
    return (
      <EmptyState
        title="No quizzes yet"
        description="Your quiz results will appear here after your first attempt."
        className="py-8"
      />
    )
  }
  return (
    <ul className="divide-y rounded-xl border bg-card">
      {attempts.map((attempt) => (
        <li key={attempt.id} className="flex flex-col gap-1.5 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium text-ink">{attempt.topic_name}</span>
            <time dateTime={attempt.created_at} title={formatDateTime(attempt.created_at)} className="text-xs text-muted-foreground">
              {timeAgo(attempt.created_at)}
            </time>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm">
            <span className="font-semibold text-ink tabular-nums">
              {attempt.score}/{attempt.total}
            </span>
            {attempt.counted ? (
              <Badge className={attempt.passed ? 'bg-status-completed text-ink' : 'bg-status-in-progress text-ink'}>
                {attempt.passed ? 'Passed' : 'Needs retry'}
              </Badge>
            ) : (
              <Badge variant="destructive" title={`Integrity score ${attempt.integrity_score}`}>
                <ShieldAlert aria-hidden="true" />
                Flagged, didn't count
              </Badge>
            )}
            {attempt.counted && (
              <span className="inline-flex items-center gap-1 text-body tabular-nums">
                <span className="sr-only">Mastery</span>
                {formatPercent(attempt.mastery_before)}
                <ArrowRight aria-hidden="true" className="size-3.5" />
                <span className="sr-only">to</span>
                {formatPercent(attempt.mastery_after)}
              </span>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}
