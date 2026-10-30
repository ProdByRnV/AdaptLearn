import { cn } from 'cn'

import { StatusDot } from '@/components/topics/StatusDot'
import { formatPercent } from '@/lib/format'
import { TOPIC_STATUS, TOPIC_STATUS_ORDER } from '@/lib/topic-status'
import { difficultyLabel } from '@/lib/topics'

/**
 * The graph as text: every topic grouped by status, each one a button that opens the same detail
 * panel. The keyboard and screen-reader way through the curriculum, since the canvas is visual only.
 * With `domainNames` (the whole map), each topic also names the domain that defines it.
 */
export function TopicList({ topics, selectedId, onSelect, domainNames = null }) {
  return (
    <div className="flex flex-col gap-6">
      {TOPIC_STATUS_ORDER.map((status) => {
        const group = topics.filter((t) => t.status === status)
        if (group.length === 0) return null
        const id = `list-${status}`
        return (
          <section key={status} aria-labelledby={id} className="flex flex-col gap-2">
            <h2 id={id} className="flex items-center gap-2 text-sm font-semibold text-ink">
              <StatusDot status={status} />
              {TOPIC_STATUS[status].label}{' '}
              <span className="font-normal text-muted-foreground">({group.length})</span>
            </h2>
            <ul className="grid gap-2 sm:grid-cols-2">
              {group.map((topic) => (
                <li key={topic.id}>
                  <button
                    type="button"
                    aria-current={topic.id === selectedId ? 'true' : undefined}
                    onClick={() => onSelect(topic.id)}
                    className={cn(
                      'flex w-full items-center justify-between gap-3 rounded-lg border bg-card px-3 py-2.5 text-left text-sm transition-colors',
                      'hover:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                      topic.id === selectedId && 'border-primary bg-accent/50',
                    )}
                  >
                    <span className="font-medium text-ink">{topic.name}</span>
                    <span className={cn('shrink-0 text-xs', topic.id === selectedId ? 'text-body' : 'text-muted-foreground')}>
                      {domainNames && `${domainNames.get(topic.home_domain) ?? topic.home_domain} · `}
                      {difficultyLabel(topic.difficulty)} · {formatPercent(topic.mastery)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
