import { useId } from 'react'
import { cn } from 'cn'

import { Progress } from '@/components/ui/progress'

/** A labelled bar for a percentage (0-100), e.g. topic mastery. */
export function ProgressBar({ value, label, showValue = true, className, barClassName }) {
  const id = useId()
  const percent = Math.min(100, Math.max(0, Math.round(Number(value) || 0)))
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {(label || showValue) && (
        <div className="flex items-baseline justify-between gap-2 text-sm">
          {label && (
            <span id={id} className="truncate text-body">
              {label}
            </span>
          )}
          {showValue && <span className="font-medium tabular-nums text-ink">{percent}%</span>}
        </div>
      )}
      <Progress value={percent} aria-labelledby={label ? id : undefined} className={cn('h-2', barClassName)} />
    </div>
  )
}
