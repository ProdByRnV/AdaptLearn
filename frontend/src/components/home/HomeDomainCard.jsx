import { ArrowRight, PartyPopper } from 'lucide-react'
import { Link } from 'react-router'

import { ProgressBar } from '@/components/common/ProgressBar'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { domainPath } from '@/lib/domains'

/** A joined domain on the home page: progress, the next topic, and the way in. */
export function HomeDomainCard({ domain }) {
  const headingId = `home-domain-${domain.id}-heading`
  return (
    <Card role="article" aria-labelledby={headingId} className="h-full gap-4 px-5 py-5">
      <div className="flex flex-col gap-1">
        <h3 id={headingId} className="text-base font-semibold text-ink">
          {domain.name}
        </h3>
        <p className="text-xs text-muted-foreground">
          {domain.completed_topics} of {domain.total_topics} topics completed
        </p>
      </div>
      <ProgressBar value={domain.progress_percent} label="Progress" />
      <p className="text-sm text-body">
        <NextStep domain={domain} />
      </p>
      <div className="mt-auto">
        {domain.onboarded ? (
          <Button asChild variant="outline" className="h-9 w-full">
            <Link to={domainPath(domain.id)} aria-label={`Open dashboard: ${domain.name}`}>
              Open dashboard
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        ) : (
          <Button asChild className="h-9 w-full">
            <Link to={domainPath(domain.id, 'onboarding')} aria-label={`Finish setting up ${domain.name}`}>
              Finish setting up
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
        )}
      </div>
    </Card>
  )
}

function NextStep({ domain }) {
  if (!domain.onboarded) return 'Tell us what you already know to get your path.'
  if (domain.curriculum_complete) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <PartyPopper aria-hidden="true" className="size-4 text-primary" />
        Every topic completed
      </span>
    )
  }
  if (domain.up_next) {
    return (
      <>
        Next: <span className="font-medium text-ink">{domain.up_next.name}</span>
      </>
    )
  }
  return "Finish the topics you're working on to unlock the next ones."
}
