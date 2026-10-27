import { AlertTriangle, RotateCw } from 'lucide-react'
import { cn } from 'cn'

import { Logo } from '@/components/layout/Logo'
import { Button } from '@/components/ui/button'

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  action,
  headingLevel = 2,
  className,
}) {
  const Heading = `h${headingLevel}`
  return (
    <div
      role="alert"
      className={cn('flex flex-col items-center justify-center gap-3 px-4 py-12 text-center', className)}
    >
      <div className="flex size-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle aria-hidden="true" className="size-5" />
      </div>
      <Heading className="text-base font-semibold text-ink">{title}</Heading>
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

/** The whole page is the error (startup, crashes): branded, with the title as the page heading. */
export function FullPageError(props) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 px-4">
      <Logo markClassName="size-8" />
      <ErrorState headingLevel={1} {...props} className={cn('py-6', props.className)} />
    </div>
  )
}
