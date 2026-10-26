import { AlertCircle } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'

/** Form-level error (wrong password, server unreachable, ...). Announced as soon as it appears. */
export function FormAlert({ message }) {
  if (!message) return null
  return (
    <Alert variant="destructive" className="border-destructive/30 bg-destructive/5">
      <AlertCircle aria-hidden="true" />
      <AlertDescription className="text-destructive">{message}</AlertDescription>
    </Alert>
  )
}
