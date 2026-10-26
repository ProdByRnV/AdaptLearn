import { Inbox } from 'lucide-react'
import { cn } from 'cn'

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-input bg-card px-6 py-12 text-center',
        className,
      )}
    >
      <div className="flex size-11 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Icon aria-hidden="true" className="size-5" />
      </div>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {description && <p className="max-w-md text-sm text-body">{description}</p>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}
