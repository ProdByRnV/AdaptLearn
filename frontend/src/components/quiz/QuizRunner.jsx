import { AlertTriangle, Info, Maximize, ShieldCheck, TimerOff } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { cn } from 'cn'

import { ErrorState } from '@/components/common/ErrorState'
import { Loader } from '@/components/common/Loader'
import { LogoMark } from '@/components/layout/Logo'
import { QuestionCard } from '@/components/quiz/QuestionCard'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useNow } from '@/hooks/useNow'
import { formatClock } from '@/lib/format'
import { fullscreenSupported } from '@/lib/proctoring'

/** The quiz while it runs: a focused, full-window page with the timer and monitoring notices. */
export function QuizRunner({ session }) {
  const { quiz, question, stage, busy, stepError, notice, selected, proctor, fullscreenDenied } = session
  const now = useNow()
  const seconds = question
    ? Math.min(question.seconds_remaining, Math.max(0, Math.ceil((question.endsAt - now) / 1000)))
    : null
  const submitting = stage === 'submitting'
  const timedOut = busy === 'timeout'

  // Reaching zero ends the question once: the selected answer is submitted, or it times out.
  const expiredFor = useRef(null)
  const { expire } = session
  useEffect(() => {
    if (seconds !== 0 || submitting || expiredFor.current === question.question_id) return
    expiredFor.current = question.question_id
    expire()
  }, [seconds, submitting, question, expire])

  const rules = Object.fromEntries(quiz.proctoring.rules.map((rule) => [rule.code, rule]))
  const answered = question ? question.number - 1 : quiz.answered_questions

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <div className="sticky top-0 z-10 border-b bg-card">
        <div className="mx-auto flex h-14 w-full max-w-3xl items-center gap-3 px-4">
          <LogoMark className="size-7 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-ink">{quiz.topic.name}</p>
            <p className="text-xs text-muted-foreground">
              {submitting
                ? 'Submitting'
                : `Question ${question?.number ?? answered + 1} of ${quiz.total_questions}`}
            </p>
          </div>
          <span className="hidden items-center gap-1.5 rounded-full bg-accent px-2.5 py-1 text-xs font-medium text-accent-foreground sm:inline-flex">
            <ShieldCheck aria-hidden="true" className="size-3.5" />
            Proctored
          </span>
          {question && !submitting && <Countdown seconds={seconds} />}
        </div>
        <TimeBar
          fraction={question && !submitting ? seconds / quiz.seconds_per_question : 0}
          seconds={seconds}
        />
      </div>

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6 sm:py-8">
        <Steps total={quiz.total_questions} done={submitting ? quiz.total_questions : answered} />

        {proctor.fullscreenLost && (
          <Alert variant="destructive">
            <AlertTriangle aria-hidden="true" />
            <AlertTitle>You left fullscreen</AlertTitle>
            <AlertDescription>
              <p>This was recorded. Return to fullscreen to keep your integrity score up.</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={proctor.returnToFullscreen}>
                <Maximize aria-hidden="true" />
                Return to fullscreen
              </Button>
            </AlertDescription>
          </Alert>
        )}
        {fullscreenDenied && !proctor.fullscreenLost && (
          <Alert role="status">
            <Info aria-hidden="true" />
            <AlertTitle className="text-ink">Fullscreen isn't available</AlertTitle>
            <AlertDescription className="text-body">
              <p>The quiz continues in this window. Stay on this page until you finish.</p>
              {fullscreenSupported() && (
                <Button variant="outline" size="sm" className="mt-2" onClick={proctor.returnToFullscreen}>
                  <Maximize aria-hidden="true" />
                  Try fullscreen again
                </Button>
              )}
            </AlertDescription>
          </Alert>
        )}
        <RecordedEvent event={proctor.lastEvent} rules={rules} />
        {notice && (
          <Alert role="status" className="border-status-in-progress/60 bg-status-in-progress/10">
            <TimerOff aria-hidden="true" />
            <AlertDescription className="text-body">{notice}</AlertDescription>
          </Alert>
        )}

        {submitting && !stepError ? (
          <Loader label="Scoring your quiz…" />
        ) : stepError ? (
          <ErrorState
            title={submitting ? "Couldn't submit your quiz" : "Couldn't reach the server"}
            message={`${stepError.message} ${submitting ? 'Nothing was lost; try again.' : 'The timer keeps running on the server.'}`}
            onRetry={stepError.retry}
            className="rounded-xl border bg-card"
          />
        ) : !question || busy === 'next' ? (
          <Loader label="Loading question…" />
        ) : (
          <>
            {timedOut && (
              <Alert role="status" className="border-status-in-progress/60 bg-status-in-progress/10">
                <TimerOff aria-hidden="true" />
                <AlertTitle className="text-ink">Time's up</AlertTitle>
                <AlertDescription className="text-body">
                  {question.number === question.total ? 'Finishing your quiz…' : 'Moving to the next question…'}
                </AlertDescription>
              </Alert>
            )}
            <QuestionCard
              question={question}
              selected={selected}
              onSelect={session.select}
              onLockIn={session.lockIn}
              ready={now >= question.readyAt}
              busy={busy}
              timedOut={timedOut}
            />
          </>
        )}
      </div>
    </div>
  )
}

function Countdown({ seconds }) {
  const tone = seconds <= 5 ? 'text-destructive' : seconds <= 15 ? 'text-ink bg-status-in-progress/25' : 'text-ink'
  return (
    <>
      <span
        role="timer"
        aria-label={`Time left: ${seconds} seconds`}
        className={cn('rounded-lg bg-muted px-2.5 py-1 text-base font-semibold tabular-nums', tone)}
      >
        {formatClock(seconds)}
      </span>
      {/* Announced once per question, not every second. */}
      <span className="sr-only" aria-live="assertive">
        {seconds > 0 && seconds <= 10 ? '10 seconds left' : ''}
      </span>
    </>
  )
}

function TimeBar({ fraction, seconds }) {
  const color = seconds !== null && seconds <= 5 ? 'bg-destructive' : seconds !== null && seconds <= 15 ? 'bg-status-in-progress' : 'bg-primary'
  return (
    <div aria-hidden="true" className="h-1 w-full bg-muted">
      <div
        className={cn('h-full transition-[width] duration-300 ease-linear', color)}
        style={{ width: `${Math.min(100, Math.max(0, fraction * 100))}%` }}
      />
    </div>
  )
}

function Steps({ total, done }) {
  return (
    <ol aria-label="Quiz progress" className="flex gap-1.5">
      {Array.from({ length: total }, (_, i) => (
        <li
          key={i}
          className={cn('h-1.5 flex-1 rounded-full', i < done ? 'bg-primary' : i === done ? 'bg-primary/40' : 'bg-muted')}
        >
          <span className="sr-only">
            Question {i + 1}: {i < done ? 'done' : i === done ? 'current' : 'to come'}
          </span>
        </li>
      ))}
    </ol>
  )
}

/** Tells the learner what was just recorded, so the integrity score is never a surprise. */
function RecordedEvent({ event, rules }) {
  const rule = event && rules[event.type]
  return (
    <p role="status" className={cn('text-sm', rule ? 'rounded-lg bg-destructive/10 px-3 py-2 text-destructive' : 'sr-only')}>
      {rule ? `Recorded: ${rule.message} (−${rule.penalty} integrity).` : ''}
    </p>
  )
}
