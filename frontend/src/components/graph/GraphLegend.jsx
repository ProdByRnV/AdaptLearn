import { ArrowRight } from 'lucide-react'

import { StatusDot } from '@/components/topics/StatusDot'
import { TOPIC_STATUS, TOPIC_STATUS_ORDER } from '@/lib/topic-status'

// The mark drawn inside each node, so the states don't depend on colour alone.
const MARKS = {
  completed: 'tick',
  in_progress: 'mastery ring',
  unlocked: 'outlined',
  locked: 'padlock',
}

/** What the colours, marks and arrows mean, with how many topics are in each state. */
export function GraphLegend({ counts }) {
  return (
    <ul aria-label="Legend" className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
      {TOPIC_STATUS_ORDER.map((status) => (
        <li key={status} className="flex items-center gap-2">
          <StatusDot status={status} className="size-3" />
          <span className="text-ink">{TOPIC_STATUS[status].label}</span>
          <span className="text-muted-foreground">
            {counts[status]}
            <span className="sr-only"> topics, shown {MARKS[status]}</span>
          </span>
        </li>
      ))}
      <li className="flex items-center gap-2 text-muted-foreground">
        <span aria-hidden="true" className="inline-flex items-center">
          <span className="h-px w-4 bg-input" />
          <ArrowRight className="-ml-1 size-3.5 text-input" />
        </span>
        Prerequisite to the topic it unlocks
      </li>
    </ul>
  )
}
