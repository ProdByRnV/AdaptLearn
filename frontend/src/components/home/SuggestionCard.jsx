import { HeadStart } from '@/components/domains/HeadStart'
import { JoinButton } from '@/components/domains/JoinButton'
import { Card } from '@/components/ui/card'

/** A domain the learner hasn't joined but already has a head start in. */
export function SuggestionCard({ domain, joining, error, onJoin }) {
  const headingId = `suggestion-${domain.id}-heading`
  return (
    <Card role="article" aria-labelledby={headingId} className="h-full gap-3 px-5 py-5">
      <div className="flex flex-col gap-1">
        <h3 id={headingId} className="text-base font-semibold text-ink">
          {domain.name}
        </h3>
        <p className="line-clamp-2 text-sm text-body">{domain.description}</p>
      </div>
      <HeadStart domain={domain} className="flex flex-col gap-1 text-xs text-muted-foreground" />
      <div className="mt-auto flex flex-col gap-2 pt-1">
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <JoinButton domain={domain} joining={joining} onJoin={onJoin} className="w-full" />
      </div>
    </Card>
  )
}
