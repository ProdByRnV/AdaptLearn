import { ArrowRight, Clock, Hourglass, ListChecks, Loader2, Lock, ShieldCheck, Trophy } from 'lucide-react'
import { Link } from 'react-router'

import { TopicStatusBadge } from '@/components/topics/TopicStatusBadge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useNow } from '@/hooks/useNow'
import { formatClock, formatPercent } from '@/lib/format'
import { difficultyLabel, listNames } from '@/lib/topics'

// PRD 6.2: three questions per quiz, two correct to pass.
const FORMAT = [
  { icon: ListChecks, text: '3 multiple-choice questions, shown one at a time.' },
  { icon: Clock, text: "Each question has its own timer. Answers can't be changed once locked in." },
  { icon: Trophy, text: 'Answer 2 of 3 correctly to pass and raise your mastery.' },
  {
    icon: ShieldCheck,
    text: "The quiz is proctored. It runs fullscreen, and switching tabs, leaving fullscreen, copying or pasting lower your integrity score. A low score means the attempt doesn't count.",
  },
]

/** Before a quiz exists: the topic, the format, and the button that generates the questions. */
export function QuizIntro({ topic, prerequisiteNames, otherActive, startError, preparing, onPrepare }) {
  const locked = topic.status === 'locked'

  return (
    <div className="flex flex-col gap-4">
      {otherActive && (
        <Alert role="status" className="border-status-in-progress/60 bg-status-in-progress/10">
          <Hourglass aria-hidden="true" />
          <AlertTitle className="text-ink">You have an unfinished quiz on {otherActive.topic.name}</AlertTitle>
          <AlertDescription className="text-body">
            <p>
              {otherActive.answered_questions} of {otherActive.total_questions} questions answered. Starting this quiz
              abandons it, and it won't count.
            </p>
            <Link to={`/quiz/${encodeURIComponent(otherActive.topic.id)}`} className="font-medium text-primary">
              Resume {otherActive.topic.name} instead
            </Link>
          </AlertDescription>
        </Alert>
      )}

      <Card className="gap-6 px-5 py-6 sm:px-6">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
          <TopicStatusBadge status={topic.status} />
          <span className="text-muted-foreground">{difficultyLabel(topic.difficulty)}</span>
          <span className="text-muted-foreground">Mastery {formatPercent(topic.mastery)}</span>
        </div>

        <section aria-labelledby="format-heading" className="flex flex-col gap-3">
          <h2 id="format-heading" className="text-base font-semibold text-ink">
            How the quiz works
          </h2>
          <ul className="flex flex-col gap-3">
            {FORMAT.map(({ icon: Icon, text }) => (
              <li key={text} className="flex gap-3 text-sm text-body">
                <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" />
                {text}
              </li>
            ))}
          </ul>
          <p className="text-sm text-muted-foreground">You'll see the full integrity rules before the first question.</p>
        </section>

        {startError && <StartError error={startError} />}

        {locked ? (
          <Alert role="status">
            <Lock aria-hidden="true" />
            <AlertTitle className="text-ink">This topic is locked</AlertTitle>
            <AlertDescription className="text-body">
              {prerequisiteNames.length > 0
                ? `Complete ${listNames(prerequisiteNames, 4)} first.`
                : 'Complete its prerequisites first.'}{' '}
              <Link to="/dashboard" className="font-medium text-primary">
                Back to dashboard
              </Link>
            </AlertDescription>
          </Alert>
        ) : (
          <PrepareButton
            preparing={preparing}
            retryAt={startError?.retryAt}
            retryAfter={startError?.retryAfter}
            onPrepare={onPrepare}
          />
        )}
      </Card>
    </div>
  )
}

function PrepareButton({ preparing, retryAt, retryAfter, onPrepare }) {
  const now = useNow(Boolean(retryAt), 1000)
  // Capped at Retry-After: `now` can lag by up to one tick.
  const wait = retryAt ? Math.min(retryAfter, Math.max(0, Math.ceil((retryAt - now) / 1000))) : 0

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <Button onClick={onPrepare} disabled={preparing || wait > 0} className="h-10 px-4">
        {preparing ? (
          <>
            <Loader2 aria-hidden="true" className="animate-spin" />
            Preparing your questions…
          </>
        ) : (
          <>
            Prepare quiz
            <ArrowRight aria-hidden="true" />
          </>
        )}
      </Button>
      {wait > 0 && (
        <p className="text-sm text-muted-foreground">
          You can start another quiz in <span className="font-medium tabular-nums text-ink">{formatClock(wait)}</span>.
        </p>
      )}
    </div>
  )
}

const START_ERROR_TITLES = {
  403: 'This topic is locked',
  404: 'Topic not found',
  429: 'Quiz limit reached',
  503: 'Quiz generation is unavailable',
}

function StartError({ error }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>{START_ERROR_TITLES[error.status] ?? "Couldn't create the quiz"}</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
    </Alert>
  )
}
