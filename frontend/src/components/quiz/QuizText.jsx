import { cn } from 'cn'

import { splitCode } from '@/lib/format'

/**
 * Quiz text with its code shown as code. Only phrasing elements are used, so it can sit inside a
 * heading or a label; a fenced block is a <code> displayed as a block that scrolls sideways.
 */
export function QuizText({ text, className }) {
  return (
    <span className={cn('whitespace-pre-line', className)}>
      {splitCode(text).map((part, index) =>
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
        ) : (
          part.value
        ),
      )}
    </span>
  )
}
