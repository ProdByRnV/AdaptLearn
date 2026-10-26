import { useId } from 'react'
import { cn } from 'cn'

/**
 * One selectable topic. The whole card is the checkbox's label, so it can be clicked anywhere and
 * used with the keyboard (Tab, Space) like any checkbox. Screen readers hear the topic name as the
 * label, then the note (why it is ticked) and the description.
 *
 * state: "selected" | "implied" (ticked because a selected topic needs it) | "completed" | "available"
 */
export function TopicOption({ topic, state, note, onToggle }) {
  const id = useId()
  const checked = state !== 'available'
  const fixed = state === 'implied' || state === 'completed'

  return (
    <label
      className={cn(
        'flex h-full gap-3 rounded-xl border bg-card p-4 transition-colors',
        'has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50',
        state === 'selected' && 'border-primary bg-accent/50',
        fixed && 'border-dashed border-primary/50 bg-accent/25',
        fixed ? 'cursor-default' : 'cursor-pointer',
        state === 'available' && 'hover:border-input hover:bg-muted/50',
      )}
    >
      <input
        type="checkbox"
        name="known"
        value={topic.id}
        checked={checked}
        // aria-disabled rather than disabled: the tick keeps the brand colour instead of turning
        // grey, and the box stays focusable so screen readers can still hear why it is ticked.
        aria-disabled={fixed || undefined}
        onChange={() => !fixed && onToggle(topic.id)}
        aria-labelledby={`${id}-name`}
        aria-describedby={note ? `${id}-note ${id}-description` : `${id}-description`}
        className="mt-0.5 size-4 shrink-0 accent-primary"
      />
      <span className="flex min-w-0 flex-col gap-1">
        <span id={`${id}-name`} className="font-medium text-ink">
          {topic.name}
        </span>
        <span id={`${id}-description`} className="line-clamp-2 text-sm text-body">
          {topic.description}
        </span>
        {note && (
          <span id={`${id}-note`} className="text-xs font-medium text-primary-dark">
            {note}
          </span>
        )}
      </span>
    </label>
  )
}
