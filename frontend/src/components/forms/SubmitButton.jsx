import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'

export function SubmitButton({ submitting, children, submittingLabel }) {
  return (
    <Button type="submit" size="lg" className="h-10 w-full" disabled={submitting}>
      {submitting && <Loader2 aria-hidden="true" className="animate-spin" />}
      {submitting ? submittingLabel : children}
    </Button>
  )
}
