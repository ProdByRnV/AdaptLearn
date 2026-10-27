import { cn } from 'cn'

import { Card } from '@/components/ui/card'

/** One headline number. `children` holds optional extra detail (a bar, a note). */
export function StatCard({ label, value, detail, icon: Icon, className, children }) {
  return (
    <Card className={cn('gap-2 px-4 py-4', className)}>
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-body">{label}</h3>
        {Icon && <Icon aria-hidden="true" className="size-4 text-primary" />}
      </div>
      <p className="text-2xl font-semibold tracking-tight text-ink tabular-nums">{value}</p>
      {detail && <p className="text-xs text-muted-foreground">{detail}</p>}
      {children}
    </Card>
  )
}
