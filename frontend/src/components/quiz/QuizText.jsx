import { cn } from 'cn'

import { Maths } from '@/components/quiz/Maths'
import { splitQuizText } from '@/lib/format'

/**
 * Quiz text with its code shown as code and its maths drawn as maths. Only phrasing elements are
 * used, so it can sit inside a heading or a label; a fenced block is a <code> displayed as a block
 * that scrolls sideways, and so is a displayed formula.
 */
export function QuizText({ text, className }) {
  return (
    <span className={cn('whitespace-pre-line', className)}>
      {splitQuizText(text).map((part, index) =>
        part.kind === 'block' ? (
          <code
            key={index}
            className="my-2 block overflow-x-auto rounded-lg bg-ink px-3 py-2.5 font-mono text-[0.8125rem] leading-relaxed font-normal whitespace-pre text-accent-on-dark"
          >
            {part.value}
          </code>
        ) : part.kind === 'code' ? (
          <code key={index} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.9em] font-normal">
            {part.value}
          </code>
        ) : part.kind === 'maths' || part.kind === 'mathsBlock' ? (
          <Maths key={index} tex={part.value} display={part.kind === 'mathsBlock'} />
        ) : (
          part.value
        ),
      )}
    </span>
  )
}
