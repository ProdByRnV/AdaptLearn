import { getErrorMessage } from '@/api/client'
import { fetchCatalogue } from '@/api/domains'
import { ErrorState } from '@/components/common/ErrorState'
import { PageHeader } from '@/components/common/PageHeader'
import { DomainCard } from '@/components/domains/DomainCard'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { useJoinDomain } from '@/hooks/useJoinDomain'

/**
 * The domain catalogue: every domain with its size and the learner's standing. Joining a domain
 * leads straight into its onboarding; topics shared with domains already studied are counted there.
 */
export default function Domains() {
  const { data, error, loading, reload } = useApiData(fetchCatalogue)
  const { join, joining, error: joinError } = useJoinDomain()
  const joinedAny = data?.domains.some((d) => d.joined)

  return (
    <>
      <PageHeader
        title="Domains"
        description={
          data && !joinedAny
            ? "Choose a domain to start. We'll ask what you already know, so you start in the right place."
            : 'Join as many as you like. Topics shared between domains count in each, so your progress carries over.'
        }
      />
      {loading && (
        <div role="status" aria-label="Loading domains" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      )}
      {error && (
        <ErrorState
          title="Couldn't load the domains"
          message={getErrorMessage(error)}
          onRetry={reload}
          className="rounded-xl border bg-card"
        />
      )}
      {data && (
        <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.domains.map((domain) => (
            <li key={domain.id}>
              <DomainCard
                domain={domain}
                joining={joining}
                error={joinError?.domainId === domain.id ? joinError.message : null}
                onJoin={join}
              />
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
