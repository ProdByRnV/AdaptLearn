import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { fetchTopicGraph, markKnownTopics } from '@/api/topics'
import { getErrorMessage } from '@/api/client'
import { ErrorState } from '@/components/common/ErrorState'
import { SelectionBar } from '@/components/onboarding/SelectionBar'
import { TopicOption } from '@/components/onboarding/TopicOption'
import { Skeleton } from '@/components/ui/skeleton'
import { useApiData } from '@/hooks/useApiData'
import { difficultyLabel, domainLabel, groupByDifficulty, impliedPrerequisites, listNames } from '@/lib/topics'

// US-04: the wording the PRD requires on this screen.
const EXPLANATION =
  'Choose topics you already feel comfortable with. AdaptLearn will skip them and start from the right place.'

export default function Onboarding() {
  const { data, error, loading, reload } = useApiData(fetchTopicGraph)

  return (
    <>
      <header className="mb-8 max-w-2xl">
        <div className="text-sm font-semibold tracking-wide text-primary uppercase">
          {data ? domainLabel(data.domain) : loading ? <Skeleton className="h-4 w-32" /> : null}
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
      {data && <TopicPicker topics={data.nodes} />}
    </>
  )
}

function TopicPicker({ topics }) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(() => new Set())
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  const byId = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics])
  const groups = useMemo(() => groupByDifficulty(topics), [topics])
  // Topics already completed (a returning learner) stay ticked and aren't counted again.
  const completed = useMemo(() => new Set(topics.filter((t) => t.status === 'completed').map((t) => t.id)), [topics])
  const implied = useMemo(() => impliedPrerequisites(byId, selected, completed), [byId, selected, completed])

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

  function noteFor(id) {
    if (completed.has(id)) return 'Already completed'
    if (implied.has(id)) return `Included: needed for ${listNames(implied.get(id).map((s) => byId.get(s).name))}`
    return null
  }

  async function submit() {
    // A returning learner adding nothing: there is nothing to save.
    if (selected.size === 0 && completed.size > 0) {
      navigate('/dashboard', { replace: true })
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    try {
      // Only the explicit choices: the server adds their prerequisites itself.
      const result = await markKnownTopics([...selected])
      navigate('/dashboard', {
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
      : completed.size > 0
        ? 'Continue to dashboard'
        : 'Start from the beginning'

  return (
    <>
      {completed.size > 0 && (
        <p className="mb-6 rounded-lg bg-muted px-3 py-2 text-sm text-body">
          Topics you have already completed are ticked. Add any others you know.
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
