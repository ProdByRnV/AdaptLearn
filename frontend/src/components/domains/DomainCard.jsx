import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router'

import { ProgressBar } from '@/components/common/ProgressBar'
import { HeadStart } from '@/components/domains/HeadStart'
import { JoinButton } from '@/components/domains/JoinButton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { domainPath } from '@/lib/domains'

/**
 * A domain in the catalogue: what it covers, how big it is, the learner's standing and head start,
 * and the next step: join it, finish setting it up, or open it.
 */
export function DomainCard({ domain, joining, error, onJoin }) {
  const headingId = `domain-${domain.id}-heading`
  const started = domain.joined || domain.completed_topics > 0
  return (
    <Card role="article" aria-labelledby={headingId} className="h-full gap-4 px-5 py-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 id={headingId} className="text-lg font-semibold text-ink">
          {domain.name}
        </h2>
        <DomainBadge domain={domain} />
      </div>
      <p className="text-sm text-body">{domain.description}</p>
      <p className="text-xs text-muted-foreground">
        {domain.total_topics} {domain.total_topics === 1 ? 'topic' : 'topics'}
        {domain.completed_topics > 0 && ` · ${domain.completed_topics} completed`}
      </p>
      {started && <ProgressBar value={domain.progress_percent} label="Progress" />}
      {!domain.joined && <HeadStart domain={domain} />}

      <div className="mt-auto flex flex-col gap-2 pt-1">
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <DomainActions domain={domain} joining={joining} onJoin={onJoin} />
        </div>
      </div>
    </Card>
  )
}

function DomainBadge({ domain }) {
  if (domain.curriculum_complete) return <Badge className="bg-status-completed text-ink">Completed</Badge>
  if (domain.joined) return <Badge variant="secondary">Joined</Badge>
  if (domain.suggested) return <Badge className="bg-accent text-accent-foreground">Head start</Badge>
  return null
}

function DomainActions({ domain, joining, onJoin }) {
  if (!domain.joined) {
    return (
      <>
        <JoinButton domain={domain} joining={joining} onJoin={onJoin} />
        <Button asChild variant="outline" className="h-9">
          <Link to={domainPath(domain.id, 'graph')} aria-label={`Preview topics: ${domain.name}`}>
            Preview topics
          </Link>
        </Button>
      </>
    )
  }
  if (!domain.onboarded) {
    return (
      <Button asChild className="h-9">
        <Link to={domainPath(domain.id, 'onboarding')} aria-label={`Finish setting up ${domain.name}`}>
          Finish setting up
          <ArrowRight aria-hidden="true" />
        </Link>
      </Button>
    )
  }
  return (
    <Button asChild className="h-9">
      <Link to={domainPath(domain.id)} aria-label={`Open ${domain.name}`}>
        Open
        <ArrowRight aria-hidden="true" />
      </Link>
    </Button>
  )
}
