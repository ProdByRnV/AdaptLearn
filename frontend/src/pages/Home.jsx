import { Compass, LayoutGrid, PartyPopper } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router'

import { getErrorMessage } from '@/api/client'
import { fetchHome } from '@/api/domains'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionHeading } from '@/components/common/SectionHeading'
import { RecentAttempts } from '@/components/dashboard/RecentAttempts'
import { RecommendedTopicCard } from '@/components/dashboard/RecommendedTopicCard'
import { HomeDomainCard } from '@/components/home/HomeDomainCard'
import { SuggestionCard } from '@/components/home/SuggestionCard'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { useAuth } from '@/hooks/useAuth'
import { useJoinDomain } from '@/hooks/useJoinDomain'
import { listNames, retryTopicIds } from '@/lib/topics'

/**
 * Everything the learner is studying, in one place: each joined domain with its progress, the
 * next topics across them, domains they already have a head start in, and their latest quizzes.
 */
export default function Home() {
  const { user } = useAuth()
  const { data, error, loading, reload } = useApiData(fetchHome)
  const names = data?.domains.map((d) => d.name) ?? []

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.username}`}
        description={
          !data
            ? 'Everything you are learning, in one place.'
            : names.length > 0
              ? `Learning ${listNames(names, 3)}`
              : "You haven't joined a domain yet."
        }
        actions={
          <Button asChild variant="outline" className="h-9">
            <Link to="/domains">
              <LayoutGrid aria-hidden="true" />
              Browse domains
            </Link>
          </Button>
        }
      />
      {loading && <HomeSkeleton />}
      {error && (
        <ErrorState
          title="Couldn't load your home page"
          message={getErrorMessage(error)}
          onRetry={reload}
          className="rounded-xl border bg-card"
        />
      )}
      {data && <HomeContent data={data} />}
    </>
  )
}

function HomeContent({ data }) {
  const { domains, up_next: upNext, suggestions, recent_attempts: attempts } = data
  const join = useJoinDomain()
  const retryIds = useMemo(() => retryTopicIds(attempts), [attempts])
  const domainNames = useMemo(() => new Map(domains.map((d) => [d.id, d.name])), [domains])

  if (domains.length === 0) {
    return (
      <EmptyState
        icon={Compass}
        title="Choose what to learn"
        description="Join a domain and we'll ask what you already know, so your path starts in the right place. You can join as many as you like."
        action={
          <Button asChild className="h-9">
            <Link to="/domains">Browse domains</Link>
          </Button>
        }
      />
    )
  }

  return (
    <div className="flex flex-col gap-10">
      <section aria-labelledby="domains-heading">
        <SectionHeading id="domains-heading" title="Your domains" />
        <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {domains.map((domain) => (
            <li key={domain.id}>
              <HomeDomainCard domain={domain} />
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="next-heading">
        <SectionHeading id="next-heading" title="Up next" hint="The easiest topics you can start now, across your domains" />
        {upNext.length > 0 ? (
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {upNext.map((topic) => (
              <li key={topic.id}>
                <RecommendedTopicCard
                  topic={topic}
                  retry={retryIds.has(topic.id)}
                  domainNames={domains.length > 1 ? topic.domains.map((id) => domainNames.get(id) ?? id) : undefined}
                />
              </li>
            ))}
          </ul>
        ) : (
          <NothingNext domains={domains} />
        )}
      </section>

      {suggestions.length > 0 && (
        <section aria-labelledby="suggestions-heading">
          <SectionHeading
            id="suggestions-heading"
            title="Suggested for you"
            hint="You already have a head start in these, from topics they share with your domains."
          />
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {suggestions.map((domain) => (
              <li key={domain.id}>
                <SuggestionCard
                  domain={domain}
                  joining={join.joining}
                  error={join.error?.domainId === domain.id ? join.error.message : null}
                  onJoin={join.join}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="recent-heading">
        <SectionHeading id="recent-heading" title="Recent quizzes" hint="Your latest attempts in any domain" />
        <RecentAttempts attempts={attempts} />
      </section>
    </div>
  )
}

/** Up next is empty: a domain still to set up, every joined domain finished, or topics to finish first. */
function NothingNext({ domains }) {
  const toSetUp = domains.filter((d) => !d.onboarded)
  if (toSetUp.length > 0) {
    return (
      <EmptyState
        title="Finish setting up to get your next topics"
        description={`Tell us what you already know in ${listNames(toSetUp.map((d) => d.name))} and your path appears here.`}
      />
    )
  }
  if (domains.every((d) => d.curriculum_complete)) {
    return (
      <EmptyState
        icon={PartyPopper}
        title="You've completed every domain you joined"
        description="Pick another domain to keep going. Topics it shares with yours are already done."
        action={
          <Button asChild variant="outline" className="h-9">
            <Link to="/domains">Browse domains</Link>
          </Button>
        }
      />
    )
  }
  return (
    <EmptyState
      title="Nothing to start right now"
      description="Finish the topics you're working on to unlock the next ones."
    />
  )
}

function HomeSkeleton() {
  return (
    <div role="status" aria-label="Loading your home page" className="flex flex-col gap-10">
      {[3, 3].map((count, group) => (
        <div key={group} className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: count }, (_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ))}
    </div>
  )
}
