import {
  CheckCircle2,
  LayoutDashboard,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trophy,
  XCircle,
} from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router'
import { cn } from 'cn'

import { ProgressBar } from '@/components/common/ProgressBar'
import { RecommendedTopicCard } from '@/components/dashboard/RecommendedTopicCard'
import { QuizText } from '@/components/quiz/QuizText'
import { ResourceList } from '@/components/topics/ResourceList'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPercent } from '@/lib/format'

const LETTERS = ['A', 'B', 'C', 'D']

/**
 * The scored quiz (PRD 6.2 and 14): score and pass/retry, the integrity verdict, mastery before and
 * after, newly unlocked topics, resources when it was failed, every answer with its explanation,
 * and what to learn next.
 */
export function QuizResult({ result, topicName, threshold, topicNames, onRetry }) {
  const headingRef = useRef(null)
  const { counted } = result.integrity
  const before = result.p_know_before * 100
  const after = result.p_know_after * 100

  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  const title = !counted ? "This attempt didn't count" : result.passed ? 'You passed' : 'Not quite yet'
  const Icon = !counted ? ShieldAlert : result.passed ? Trophy : RotateCcw

  return (
    <div className="flex flex-col gap-8">
      <Card className="gap-5 px-5 py-6 sm:px-6">
        <div className="flex items-start gap-4">
          <div
            className={cn(
              'flex size-12 shrink-0 items-center justify-center rounded-full',
              !counted
                ? 'bg-destructive/10 text-destructive'
                : result.passed
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-status-in-progress/20 text-ink',
            )}
          >
            <Icon aria-hidden="true" className="size-6" />
          </div>
          <div className="flex min-w-0 flex-col gap-1">
            <h2 ref={headingRef} tabIndex={-1} className="text-xl font-semibold text-ink outline-none">
              {title}
            </h2>
            <p className="text-sm text-body">
              You got <span className="font-semibold text-ink">{result.score} of {result.total}</span> right on{' '}
              {topicName}.
              {counted && !result.passed && ' You need 2 correct to pass.'}
            </p>
            <div className="mt-1 flex flex-wrap gap-2">
              <Badge className={result.passed ? 'bg-status-completed text-ink' : 'bg-status-in-progress text-ink'}>
                {result.passed ? 'Passed' : 'Needs retry'}
              </Badge>
              {counted && result.mastered && (
                <Badge className="bg-primary-dark text-white">
                  <Sparkles aria-hidden="true" />
                  Mastered
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded-lg bg-muted/60 px-4 py-3">
          <ProgressBar value={after} label="Mastery" />
          <p className="text-sm text-body">
            {counted
              ? `${formatPercent(before)} before this quiz, ${formatPercent(after)} now.`
              : `Unchanged at ${formatPercent(before)}, because this attempt didn't count.`}
          </p>
        </div>

        <IntegrityPanel integrity={result.integrity} threshold={threshold} />
      </Card>

      {result.newly_unlocked.length > 0 && (
        <section aria-labelledby="unlocked-heading" className="flex flex-col gap-3">
          <SectionHeading id="unlocked-heading" title="New topics unlocked" />
          <ul className="flex flex-wrap gap-2">
            {result.newly_unlocked.map((id) => (
              <li key={id}>
                <Link
                  to={`/quiz/${encodeURIComponent(id)}`}
                  className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-accent/50 px-3 py-1.5 text-sm font-medium text-primary-dark hover:bg-accent"
                >
                  <Sparkles aria-hidden="true" className="size-4" />
                  {topicNames.get(id) ?? id}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {result.recommended_resources.length > 0 && (
        <section aria-labelledby="resources-heading" className="flex flex-col gap-3">
          <SectionHeading
            id="resources-heading"
            title="Review before trying again"
            hint={
              result.needs_attention
                ? 'This topic needs attention: several attempts without much progress.'
                : 'These cover what the quiz asked about.'
            }
          />
          <Card className="px-5 py-4">
            <ResourceList resources={result.recommended_resources} />
          </Card>
        </section>
      )}

      <section aria-labelledby="review-heading" className="flex flex-col gap-3">
        <SectionHeading id="review-heading" title="Your answers" />
        <ol className="flex flex-col gap-3">
          {result.feedback.map((item, index) => (
            <AnswerReview key={index} item={item} number={index + 1} />
          ))}
        </ol>
      </section>

      {result.next_topics.length > 0 && (
        <section aria-labelledby="next-heading" className="flex flex-col gap-3">
          <SectionHeading id="next-heading" title="Up next" />
          <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {result.next_topics.map((topic) => (
              <li key={topic.id}>
                <RecommendedTopicCard topic={topic} retry={topic.id === result.topic_id && !result.passed} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-wrap gap-2">
        <Button asChild className="h-10 px-4">
          <Link to="/dashboard">
            <LayoutDashboard aria-hidden="true" />
            Back to dashboard
          </Link>
        </Button>
        {(!result.passed || !counted) && (
          <Button variant="outline" onClick={onRetry} className="h-10 px-4">
            <RotateCcw aria-hidden="true" />
            Try again
          </Button>
        )}
      </div>
    </div>
  )
}

function SectionHeading({ id, title, hint }) {
  return (
    <div className="flex flex-col gap-0.5">
      <h2 id={id} className="text-lg font-semibold text-ink">
        {title}
      </h2>
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}

function IntegrityPanel({ integrity, threshold }) {
  const verified = integrity.verdict === 'verified'
  const Icon = verified ? ShieldCheck : ShieldAlert
  return (
    <section
      aria-labelledby="integrity-heading"
      className={cn(
        'flex flex-col gap-2 rounded-lg border px-4 py-3',
        verified ? 'border-primary/30 bg-accent/40' : 'border-destructive/30 bg-destructive/5',
      )}
    >
      <h3 id="integrity-heading" className={cn('flex items-center gap-2 text-sm font-semibold', verified ? 'text-primary-dark' : 'text-destructive')}>
        <Icon aria-hidden="true" className="size-4" />
        {verified ? 'Integrity verified' : 'Flagged by proctoring'}
        <span className="font-normal text-body">· {integrity.score}/100</span>
      </h3>
      <p className="text-sm text-body">
        {verified
          ? integrity.reasons.length > 0
            ? `Some things were recorded, but the score stayed at ${threshold} or more, so the attempt counts.`
            : 'Nothing was recorded during the quiz. The attempt counts.'
          : `Attempts need an integrity score of ${threshold} or more to count. This one was recorded, but your mastery, progress and unlocks didn't change.`}
      </p>
      {integrity.reasons.length > 0 && (
        <ul className="flex flex-col gap-1 text-sm">
          {integrity.reasons.map((reason) => (
            <li key={reason.code} className="flex items-center justify-between gap-4">
              <span className="text-body">
                {reason.message}
                {reason.count > 1 && ` (×${reason.count})`}
              </span>
              <span className="shrink-0 font-medium tabular-nums text-destructive">
                −{reason.penalty}
                <span className="sr-only"> points</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function AnswerReview({ item, number }) {
  const status = item.is_correct ? 'Correct' : item.selected === null ? (item.timed_out ? 'Not answered in time' : 'Not answered') : 'Wrong'
  return (
    <li>
      <Card className="gap-3 px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-medium text-muted-foreground">Question {number}</h3>
          <Badge className={item.is_correct ? 'bg-status-completed text-ink' : 'bg-destructive/10 text-destructive'}>
            {item.is_correct ? <CheckCircle2 aria-hidden="true" /> : <XCircle aria-hidden="true" />}
            {status}
          </Badge>
        </div>
        <p className="font-medium text-ink">
          <QuizText text={item.question} />
        </p>
        <ul className="flex flex-col gap-1.5">
          {item.options.map((option, index) => {
            const correct = index === item.correct
            const chosen = index === item.selected
            return (
              <li
                key={index}
                className={cn(
                  'flex items-start gap-2.5 rounded-lg border px-3 py-2 text-sm',
                  correct ? 'border-status-completed bg-status-completed/10' : chosen ? 'border-destructive/40 bg-destructive/5' : 'border-transparent',
                )}
              >
                <span aria-hidden="true" className="w-4 shrink-0 font-semibold text-muted-foreground">
                  {LETTERS[index]}
                </span>
                <QuizText text={option} className="min-w-0 flex-1 text-ink" />
                {(correct || chosen) && (
                  <span className={cn('shrink-0 text-xs font-medium', correct ? 'text-primary-dark' : 'text-destructive')}>
                    {correct && chosen ? 'Your answer, correct' : correct ? 'Correct answer' : 'Your answer'}
                  </span>
                )}
              </li>
            )
          })}
        </ul>
        <p className="text-sm text-body">
          <span className="font-medium text-ink">Why: </span>
          <QuizText text={item.explanation} />
        </p>
      </Card>
    </li>
  )
}
