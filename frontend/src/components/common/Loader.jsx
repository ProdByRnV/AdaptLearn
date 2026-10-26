import { Loader2 } from 'lucide-react'
import { cn } from 'cn'

export function Spinner({ className, label = 'Loading' }) {
  return (
    <span role="status" className="inline-flex items-center">
      <Loader2 aria-hidden="true" className={cn('size-5 animate-spin text-primary', className)} />
      <span className="sr-only">{label}</span>
    </span>
  )
}

export function Loader({ label = 'Loading…', className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-12 text-sm text-muted-foreground', className)}>
      <Spinner className="size-6" label={label} />
      <p aria-hidden="true">{label}</p>
    </div>
  )
}

export function FullPageLoader({ label = 'Loading…' }) {
  return <Loader label={label} className="min-h-svh" />
}
