import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { fetchTopicMap, markKnownTopics } from '@/api/topics'
import { getErrorMessage } from '@/api/client'
import { ErrorState } from '@/components/common/ErrorState'
import { DomainNotFound } from '@/components/domains/DomainNotFound'
import { SelectionBar } from '@/components/onboarding/SelectionBar'
import { TopicOption } from '@/components/onboarding/TopicOption'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { domainPath } from '@/lib/domains'
import { difficultyLabel, groupByDifficulty, impliedPrerequisites, listNames } from '@/lib/topics'

// US-04: the wording the PRD requires on this screen.
const EXPLANATION =
  'Choose topics you already feel comfortable with. AdaptLearn will skip them and start from the right place.'

/**
 * Onboarding for one domain: the learner ticks the topics they already know. It reads the whole map,
 * so prerequisites from other domains are followed and named too, and topics completed through
 * another domain are already ticked. Saving records that this domain has been set up.
 */
export default function Onboarding() {
  const { domainId } = useParams()
  const { data, error, loading, reload } = useApiData(fetchTopicMap)
  const domain = data?.domains.find((d) => d.id === domainId)

  if (data && !domain) return <DomainNotFound />
  return (
    <>
      <header className="mb-8 max-w-2xl">
        <div className="text-sm font-semibold tracking-wide text-primary uppercase">
          {domain ? domain.name : loading ? <Skeleton className="h-4 w-32" /> : null}
        </div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">What do you already know?</h1>
        <p className="mt-2 text-body">{EXPLANATION}</p>
      </header>
      {loading && <TopicGridSkeleton />}
      {error && (
        <ErrorState
          title="Couldn't load the topics"
          message={getErrorMessage(error)}
          onRetry={reload}
          className="rounded-xl border bg-card"
        />
      )}
      {domain && <TopicPicker domain={domain} map={data} />}
    </>
  )
}

function TopicPicker({ domain, map }) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(() => new Set())
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  const byId = useMemo(() => new Map(map.nodes.map((t) => [t.id, t])), [map])
  const domainNames = useMemo(() => new Map(map.domains.map((d) => [d.id, d.name])), [map])
  const topics = useMemo(() => map.nodes.filter((t) => t.domains.includes(domain.id)), [map, domain])
  const groups = useMemo(() => groupByDifficulty(topics), [topics])
  // Topics already completed (in this domain or another) stay ticked and aren't counted again.
  const completed = useMemo(() => new Set(map.nodes.filter((t) => t.status === 'completed').map((t) => t.id)), [map])
  const completedHere = topics.filter((t) => completed.has(t.id)).length
  const implied = useMemo(() => impliedPrerequisites(byId, selected, completed), [byId, selected, completed])
  // Prerequisites that come from other domains have no card here, so they are listed separately.
  const impliedElsewhere = [...implied.keys()].map((id) => byId.get(id)).filter((t) => !t.domains.includes(domain.id))

  const toggle = useCallback((id) => {
    setSubmitError(null)
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  function stateOf(id) {
    if (completed.has(id)) return 'completed'
    if (selected.has(id)) return 'selected'
    if (implied.has(id)) return 'implied'
    return 'available'
  }

  function neededFor(id) {
    return listNames(implied.get(id).map((s) => byId.get(s).name))
  }

  function noteFor(id) {
    if (completed.has(id)) return 'Already completed'
    if (implied.has(id)) return `Included: needed for ${neededFor(id)}`
    return null
  }

  async function submit() {
    setSubmitting(true)
    setSubmitError(null)
    try {
      // Only the explicit choices: the server adds their prerequisites itself. Saving with nothing
      // chosen still matters, since it records that this domain has been set up.
      const result = await markKnownTopics(domain.id, [...selected])
      navigate(domainPath(domain.id), {
        replace: true,
        state: {
          onboarding: {
            knownCount: result.known_count,
            addedPrerequisites: result.added_prerequisites.map((id) => byId.get(id)?.name ?? id),
          },
        },
      })
    } catch (err) {
      setSubmitError(getErrorMessage(err, "Couldn't save your topics. Please try again."))
      setSubmitting(false)
    }
  }

  const submitLabel =
    selected.size > 0
      ? `Continue with ${selected.size + implied.size} ${selected.size + implied.size === 1 ? 'topic' : 'topics'}`
      : completedHere > 0
        ? 'Continue to dashboard'
        : 'Start from the beginning'

  return (
    <>
      {completedHere > 0 && (
        <p className="mb-6 rounded-lg bg-muted px-3 py-2 text-sm text-body">
          Topics you have already completed, here or in another domain, are ticked. Add any others you know.
        </p>
      )}
      <div className="flex flex-col gap-10">
        {groups.map(({ level, topics: items }) => (
          <section key={level} aria-labelledby={`level-${level}`}>
            <h2 id={`level-${level}`} className="mb-3 flex items-baseline gap-2 text-lg font-semibold text-ink">
              {difficultyLabel(level)}
              <span className="text-sm font-normal text-muted-foreground">
                {items.length} {items.length === 1 ? 'topic' : 'topics'}
              </span>
            </h2>
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((topic) => (
                <li key={topic.id}>
                  <TopicOption topic={topic} state={stateOf(topic.id)} note={noteFor(topic.id)} onToggle={toggle} />
                </li>
              ))}
            </ul>
          </section>
        ))}
        {impliedElsewhere.length > 0 && (
          <section aria-labelledby="other-domains-heading" className="rounded-xl border bg-card px-5 py-4">
            <h2 id="other-domains-heading" className="text-base font-semibold text-ink">
              Included from other domains
            </h2>
            <p className="mt-1 text-sm text-body">
              These come before topics you chose, so they will be marked as known too.
            </p>
            <ul className="mt-3 flex flex-col gap-1.5 text-sm">
              {impliedElsewhere.map((topic) => (
                <li key={topic.id}>
                  <span className="font-medium text-ink">{topic.name}</span>
                  <span className="text-muted-foreground">
                    {' '}
                    ({domainNames.get(topic.home_domain) ?? topic.home_domain}), needed for {neededFor(topic.id)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
      <SelectionBar
        chosen={selected.size}
        implied={implied.size}
        submitLabel={submitLabel}
        submitting={submitting}
        error={submitError}
        onClear={() => setSelected(new Set())}
        onSubmit={submit}
      />
    </>
  )
}

function TopicGridSkeleton() {
  return (
    <div role="status" aria-label="Loading topics" className="flex flex-col gap-10">
      {[6, 6].map((count, group) => (
        <div key={group}>
          <Skeleton className="mb-3 h-6 w-40" />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: count }, (_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
