import { cn } from 'cn'

const DOT = {
  completed: 'bg-status-completed',
  in_progress: 'bg-status-in-progress',
  unlocked: 'bg-status-unlocked ring-1 ring-primary',
  locked: 'bg-status-locked',
}

/** A small dot in a topic status colour (decorative: always pair it with the status in text). */
export function StatusDot({ status, className }) {
  return <span aria-hidden="true" className={cn('size-2.5 shrink-0 rounded-full', DOT[status], className)} />
}
