import { listNames } from '@/lib/topics'

/** What the learner already has in a domain they haven't joined: topics completed elsewhere, and topics that opened. */
export function HeadStart({ domain, className = 'flex flex-col gap-1 text-sm text-body' }) {
  const known = domain.known_topics.map((t) => t.name)
  const ready = domain.ready_topics.map((t) => t.name)
  if (known.length === 0 && ready.length === 0) return null
  return (
    <ul className={className}>
      {known.length > 0 && <li>Already completed: {listNames(known, 3)}</li>}
      {ready.length > 0 && <li>Ready to start: {listNames(ready, 3)}</li>}
    </ul>
  )
}
