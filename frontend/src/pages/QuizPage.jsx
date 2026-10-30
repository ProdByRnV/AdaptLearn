import { SearchX } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { Link, useBlocker, useLocation, useOutletContext, useParams } from 'react-router'

import { getErrorMessage } from '@/api/client'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Loader } from '@/components/common/Loader'
import { PageHeader } from '@/components/common/PageHeader'
import { LeaveQuizDialog } from '@/components/quiz/LeaveQuizDialog'
import { QuizEnded } from '@/components/quiz/QuizEnded'
import { QuizIntro } from '@/components/quiz/QuizIntro'
import { QuizReady } from '@/components/quiz/QuizReady'
import { QuizResult } from '@/components/quiz/QuizResult'
import { QuizRunner } from '@/components/quiz/QuizRunner'
import { Button } from '@/components/ui/button'
import { useBackLink } from '@/hooks/useBackLink'
import { useQuizSession } from '@/hooks/useQuizSession'

export default function QuizPage() {
  const { topicId } = useParams()
  // Keyed by navigation, so following a link to this same topic (e.g. "Retry quiz" from the
  // result) starts a fresh flow instead of keeping the old one.
  const { key } = useLocation()
  return <QuizFlow key={key} topicId={topicId} />
}

function QuizFlow({ topicId }) {
  const session = useQuizSession(topicId)
  const back = useBackLink()
  const { stage, graph, quiz, monitoring } = session
  const { setFocusMode } = useOutletContext() ?? {}

  const topicsById = useMemo(() => new Map((graph?.nodes ?? []).map((t) => [t.id, t])), [graph])
  const topicNames = useMemo(() => new Map([...topicsById].map(([id, t]) => [id, t.name])), [topicsById])
  const topic = topicsById.get(topicId)

  // While the quiz runs the navbar is hidden, the browser warns before a reload or close, and
  // in-app navigation (e.g. the back button) asks first.
  useEffect(() => {
    setFocusMode?.(monitoring)
    return () => setFocusMode?.(false)
  }, [monitoring, setFocusMode])

  useEffect(() => {
    if (!monitoring) return undefined
    const warn = (event) => {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [monitoring])

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) => monitoring && currentLocation.pathname !== nextLocation.pathname,
  )

  if (monitoring) {
    return (
      <>
        <QuizRunner session={session} />
        <LeaveQuizDialog blocker={blocker} />
      </>
    )
  }

  const name = quiz?.topic.name ?? topic?.name
  return (
    <div className="mx-auto w-full max-w-3xl">
      <PageHeader
        title={name ? `${name} quiz` : 'Quiz'}
        description={stage === 'result' ? 'Your result' : topic?.description}
      />
      {stage === 'loading' && <Loader label="Loading quiz…" />}
      {stage === 'load-error' && (
        <ErrorState
          title="Couldn't load the quiz"
          message={getErrorMessage(session.loadError)}
          onRetry={session.restart}
          className="rounded-xl border bg-card"
        />
      )}
      {(stage === 'intro' || stage === 'preparing') &&
        (topic ? (
          <QuizIntro
            topic={topic}
            prerequisiteNames={topic.prerequisites.map((id) => topicNames.get(id) ?? id)}
            otherActive={session.otherActive}
            startError={session.startError}
            preparing={stage === 'preparing'}
            onPrepare={session.prepare}
          />
        ) : (
          <EmptyState
            icon={SearchX}
            title="Topic not found"
            description={`There's no topic called "${topicId}" in your curriculum.`}
            action={
              <Button asChild variant="outline">
                <Link to={back.to}>{back.label}</Link>
              </Button>
            }
          />
        ))}
      {stage === 'ready' && <QuizReady quiz={quiz} onBegin={session.begin} />}
      {stage === 'result' && (
        <QuizResult
          result={session.result}
          topicName={name}
          threshold={quiz.proctoring.verified_threshold}
          topicNames={topicNames}
          onRetry={session.restart}
        />
      )}
      {stage === 'ended' && <QuizEnded reason={session.ended} onRestart={session.restart} />}
    </div>
  )
}
