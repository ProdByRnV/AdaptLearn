import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { formatPercent } from '@/lib/format'
import { TOPIC_STATUS } from '@/lib/topic-status'
import { cn } from 'cn'

const DOT = {
  completed: 'bg-status-completed',
  in_progress: 'bg-status-in-progress',
  unlocked: 'bg-status-unlocked',
  locked: 'bg-status-locked',
}

/**
 * Compact mastery bars (PRD 9.10). Topics the learner can reach are shown; locked ones are one
 * click away, so the list stays short early on.
 */
export function MasteryOverview({ items }) {
  const [showLocked, setShowLocked] = useState(false)
  const reachable = items.filter((item) => item.status !== 'locked')
  const lockedCount = items.length - reachable.length
  const visible = showLocked ? items : reachable

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card px-4 py-4">
      <ul className="flex flex-col gap-2.5">
        {visible.map((item) => (
          <li key={item.id} className="grid grid-cols-[minmax(0,1fr)_5rem_2.75rem] items-center gap-3 text-sm sm:grid-cols-[minmax(0,1fr)_8rem_2.75rem]">
            <span className="flex min-w-0 items-center gap-2">
              <span aria-hidden="true" className={cn('size-2 shrink-0 rounded-full', DOT[item.status])} />
              <span className="truncate text-body" id={`mastery-${item.id}`}>
                {item.name}
              </span>
              <span className="sr-only">({TOPIC_STATUS[item.status]?.label ?? item.status})</span>
            </span>
            <Progress value={Math.round(item.mastery)} aria-labelledby={`mastery-${item.id}`} className="h-1.5" />
            <span className={cn('text-right tabular-nums', item.mastered ? 'font-semibold text-primary' : 'text-ink')}>
              {formatPercent(item.mastery)}
            </span>
          </li>
        ))}
      </ul>
      {lockedCount > 0 && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="self-start"
          aria-expanded={showLocked}
          onClick={() => setShowLocked((v) => !v)}
        >
          {showLocked ? 'Hide locked topics' : `Show ${lockedCount} locked ${lockedCount === 1 ? 'topic' : 'topics'}`}
        </Button>
      )}
    </div>
  )
}
