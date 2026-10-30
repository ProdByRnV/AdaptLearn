import { Compass } from 'lucide-react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/common/EmptyState'
import { Button } from '@/components/ui/button'

/** A domain page for a domain that doesn't exist (an old or mistyped link). */
export function DomainNotFound() {
  return (
    <EmptyState
      icon={Compass}
      title="We couldn't find that domain"
      titleAs="h1"
      description="It may have been renamed or removed. Every domain you can study is in the catalogue."
      action={
        <Button asChild className="h-9">
          <Link to="/domains">Browse domains</Link>
        </Button>
      }
    />
  )
}
