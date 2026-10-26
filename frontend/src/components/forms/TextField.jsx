import { useId } from 'react'
import { cn } from 'cn'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

/**
 * A labelled input with an optional hint and error. The error replaces the hint and is linked
 * through aria-describedby, so screen readers read it when the field gets focus.
 */
export function FieldShell({ id, label, hint, error, children, className }) {
  const messageId = `${id}-message`
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <Label htmlFor={id} className="text-ink">
        {label}
      </Label>
      {children({ describedBy: error || hint ? messageId : undefined, invalid: Boolean(error) })}
      {error ? (
        <p id={messageId} className="text-sm text-destructive">
          {error}
        </p>
      ) : (
        hint && (
          <p id={messageId} className="text-sm text-muted-foreground">
            {hint}
          </p>
        )
      )}
    </div>
  )
}

export function TextField({ label, hint, error, className, inputClassName, ...inputProps }) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} className={className}>
      {({ describedBy, invalid }) => (
        <Input
          id={id}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          className={cn('h-10', inputClassName)}
          {...inputProps}
        />
      )}
    </FieldShell>
  )
}
