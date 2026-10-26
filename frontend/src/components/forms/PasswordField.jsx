import { Eye, EyeOff } from 'lucide-react'
import { useId, useState } from 'react'

import { FieldShell } from '@/components/forms/TextField'
import { Input } from '@/components/ui/input'

/** Password input with a show/hide toggle, so learners can check what they typed. */
export function PasswordField({ label = 'Password', hint, error, className, ...inputProps }) {
  const id = useId()
  const [visible, setVisible] = useState(false)

  return (
    <FieldShell id={id} label={label} hint={hint} error={error} className={className}>
      {({ describedBy, invalid }) => (
        <div className="relative">
          <Input
            id={id}
            type={visible ? 'text' : 'password'}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            className="h-10 pr-10"
            {...inputProps}
          />
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
            aria-pressed={visible}
            aria-controls={id}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-muted-foreground transition-colors hover:text-ink focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            {visible ? <EyeOff aria-hidden="true" className="size-4" /> : <Eye aria-hidden="true" className="size-4" />}
          </button>
        </div>
      )}
    </FieldShell>
  )
}
