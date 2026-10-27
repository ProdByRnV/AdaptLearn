import { Info, Maximize, Play } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { fullscreenSupported } from '@/lib/proctoring'

/**
 * A quiz exists but no question has been shown (or it is being resumed): the integrity rules from
 * the server, then the button that enters fullscreen and serves the first question.
 */
export function QuizReady({ quiz, onBegin }) {
  const resuming = quiz.answered_questions > 0
  const minutes = Math.max(1, Math.floor(quiz.expires_in_seconds / 60))
  const fullscreen = fullscreenSupported()
  const { verified_threshold: threshold, rules } = quiz.proctoring

  return (
    <Card className="gap-6 px-5 py-6 sm:px-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-ink">{resuming ? 'Resume your quiz' : 'Your quiz is ready'}</h2>
        <p className="text-sm text-body">
          {resuming
            ? `You've answered ${quiz.answered_questions} of ${quiz.total_questions} questions. Pick up where you left off.`
            : 'Read the rules, then start when you are ready. The timer for each question starts when it appears.'}
        </p>
      </div>

      <dl className="grid grid-cols-3 gap-3 text-center">
        <Fact label="Questions" value={quiz.total_questions} />
        <Fact label="Per question" value={`${quiz.seconds_per_question}s`} />
        <Fact label="Start within" value={`${minutes} min`} />
      </dl>

      {quiz.source === 'fallback' && (
        <Alert role="status" className="border-primary/30 bg-accent/40">
          <Info aria-hidden="true" className="text-primary" />
          <AlertTitle className="text-ink">Questions from the curated bank</AlertTitle>
          <AlertDescription className="text-body">
            AI question generation isn't available right now, so this quiz uses AdaptLearn's curated questions for
            this topic. It counts the same.
          </AlertDescription>
        </Alert>
      )}

      <section aria-labelledby="rules-heading" className="flex flex-col gap-3">
        <h3 id="rules-heading" className="text-base font-semibold text-ink">
          Integrity rules
        </h3>
        <p className="text-sm text-body">
          Your score starts at 100. The attempt counts if it stays at {threshold} or more; below that it is flagged,
          and your mastery and progress don't change. Each of these lowers it:
        </p>
        <ul className="divide-y rounded-lg border">
          {rules.map((rule) => (
            <li key={rule.code} className="flex items-center justify-between gap-4 px-3 py-2 text-sm">
              <span className="text-body">{rule.message}</span>
              <span className="shrink-0 font-medium tabular-nums text-destructive">
                −{rule.penalty}
                <span className="sr-only"> points</span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="tips-heading" className="flex flex-col gap-2">
        <h3 id="tips-heading" className="text-base font-semibold text-ink">
          Before you start
        </h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-body">
          <li>Close other tabs and apps, and disconnect any second screen.</li>
          <li>Stay on this page. {fullscreen && "Don't press Esc: it leaves fullscreen."}</li>
          <li>A question you don't answer in time counts as wrong.</li>
        </ul>
      </section>

      <Button onClick={onBegin} className="h-10 self-start px-4">
        {fullscreen ? <Maximize aria-hidden="true" /> : <Play aria-hidden="true" />}
        {fullscreen
          ? resuming
            ? 'Enter fullscreen and resume'
            : 'Enter fullscreen and start'
          : resuming
            ? 'Resume quiz'
            : 'Start quiz'}
      </Button>
    </Card>
  )
}

function Fact({ label, value }) {
  return (
    <div className="flex flex-col-reverse gap-0.5 rounded-lg bg-muted/60 px-2 py-3">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-lg font-semibold tabular-nums text-ink">{value}</dd>
    </div>
  )
}
