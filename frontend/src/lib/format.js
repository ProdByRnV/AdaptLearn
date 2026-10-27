/** Mastery and progress values arrive as percentages with one decimal (e.g. 98.9). */
export function formatPercent(value) {
  return `${Math.round(Number(value) || 0)}%`
}

const UNITS = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['week', 7 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
]

const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

/** "just now", "5 minutes ago", "yesterday", "3 weeks ago". */
export function timeAgo(iso, now = Date.now()) {
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000)
  if (!Number.isFinite(seconds)) return ''
  if (Math.abs(seconds) < 60) return 'just now'
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit)
  }
  return 'just now'
}

/** Full date and time for a tooltip, in the learner's locale. */
export function formatDateTime(iso) {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

/** A countdown as m:ss ("1:05", "0:09"). Negative or invalid values show 0:00. */
export function formatClock(totalSeconds) {
  const seconds = Math.max(0, Math.floor(Number(totalSeconds) || 0))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

const FENCE = /```[\w+-]*[^\S\n]*\n?([\s\S]*?)\n?```/g
const INLINE = /`([^`\n]+)`/g

/**
 * Split quiz text into plain text, inline code (`x`) and fenced code blocks (```lang ... ```),
 * which AI questions use for snippets. Returns [{kind: "text"|"code"|"block", value}].
 */
export function splitCode(text = '') {
  const parts = []
  const pushText = (value) => {
    let last = 0
    for (const match of value.matchAll(INLINE)) {
      if (match.index > last) parts.push({ kind: 'text', value: value.slice(last, match.index) })
      parts.push({ kind: 'code', value: match[1] })
      last = match.index + match[0].length
    }
    if (last < value.length) parts.push({ kind: 'text', value: value.slice(last) })
  }
  let last = 0
  for (const match of text.matchAll(FENCE)) {
    pushText(text.slice(last, match.index).replace(/\n+$/, ''))
    parts.push({ kind: 'block', value: match[1] })
    last = match.index + match[0].length
  }
  pushText(text.slice(last).replace(/^\n+/, ''))
  return parts.filter((part) => part.kind === 'block' || part.value !== '')
}
