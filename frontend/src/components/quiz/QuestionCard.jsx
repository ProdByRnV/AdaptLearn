import { Lock } from 'lucide-react'
import { useEffect, useId, useRef } from 'react'
import { cn } from 'cn'

import { QuizText } from '@/components/quiz/QuizText'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const LETTERS = ['A', 'B', 'C', 'D']

/**
 * One question. The options are native radio buttons (arrow keys move between them); the answer
 * is only sent when locked in. `ready` is false for the first few seconds, since answers faster
 * than the question can be read are penalised. The heading takes focus when a question appears,
 * so screen readers start reading it.
 */
export function QuestionCard({ question, selected, onSelect, onLockIn, ready, busy, timedOut }) {
  const id = useId()
  const headingRef = useRef(null)
  const last = question.number === question.total
  const disabled = Boolean(busy) || timedOut

  useEffect(() => {
    headingRef.current?.focus()
  }, [question.question_id])

  return (
    <Card className="gap-6 px-5 py-6 sm:px-6">
      <form
        className="flex flex-col gap-6"
        onSubmit={(event) => {
          event.preventDefault()
          if (ready && !disabled && selected !== null) onLockIn()
        }}
      >
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium tracking-wide text-primary uppercase">
            Question {question.number} of {question.total}
          </p>
          <h2
            id={`${id}-question`}
            ref={headingRef}
            tabIndex={-1}
            className="text-lg leading-snug font-semibold text-ink outline-none select-none"
          >
            <QuizText text={question.question} />
          </h2>
        </div>

        <div role="radiogroup" aria-labelledby={`${id}-question`} className="flex flex-col gap-2.5">
          {question.options.map((option, index) => {
            const checked = selected === index
            return (
              <label
                key={index}
                className={cn(
                  'flex items-start gap-3 rounded-xl border bg-card p-3.5 transition-colors select-none',
                  'has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50',
                  checked && 'border-primary bg-accent/50',
                  disabled ? 'cursor-default opacity-70' : 'cursor-pointer',
                  !checked && !disabled && 'hover:border-input hover:bg-muted/50',
                )}
              >
                <input
                  type="radio"
                  name={`${id}-answer`}
                  value={index}
                  checked={checked}
                  disabled={disabled}
                  onChange={() => onSelect(index)}
                  className="sr-only"
                />
                <span
                  aria-hidden="true"
                  className={cn(
                    'flex size-7 shrink-0 items-center justify-center rounded-full border text-sm font-semibold',
                    checked ? 'border-primary bg-primary text-primary-foreground' : 'text-body',
                  )}
                >
                  {LETTERS[index]}
                </span>
                <QuizText text={option} className="min-w-0 pt-0.5 text-sm text-ink sm:text-base" />
              </label>
            )
          })}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {ready ? "Answers can't be changed once locked in." : 'Take a moment to read the question.'}
          </p>
          <Button type="submit" disabled={!ready || disabled || selected === null} className="h-10 px-4">
            <Lock aria-hidden="true" />
            {busy === 'answer' ? 'Locking in…' : last ? 'Lock in and finish' : 'Lock in answer'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
