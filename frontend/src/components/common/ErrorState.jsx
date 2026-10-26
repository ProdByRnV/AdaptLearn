import { AlertTriangle, RotateCw } from 'lucide-react'
import { cn } from 'cn'

import { Button } from '@/components/ui/button'

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  action,
  className,
}) {
  return (
    <div
      role="alert"
      className={cn('flex flex-col items-center justify-center gap-3 px-4 py-12 text-center', className)}
    >
      <div className="flex size-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle aria-hidden="true" className="size-5" />
      </div>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {message && <p className="max-w-md text-sm text-body">{message}</p>}
      {(onRetry || action) && (
        <div className="mt-1 flex flex-wrap items-center justify-center gap-2">
          {onRetry && (
            <Button variant="outline" onClick={onRetry}>
              <RotateCw aria-hidden="true" />
              {retryLabel}
            </Button>
          )}
          {action}
        </div>
      )}
    </div>
  )
}

export function FullPageError(props) {
  return <ErrorState {...props} className={cn('min-h-svh', props.className)} />
}
