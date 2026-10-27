import { describe, expect, it } from 'vitest'

import { formatPercent, timeAgo } from '@/lib/format'
import { topicAction } from '@/lib/topics'

describe('formatPercent', () => {
  it.each([
    [98.9, '99%'],
    [45.5, '46%'],
    [10, '10%'],
    [0, '0%'],
    [undefined, '0%'],
  ])('%s -> %s', (value, text) => {
    expect(formatPercent(value)).toBe(text)
  })
})

describe('timeAgo', () => {
  const now = Date.parse('2026-10-27T12:00:00Z')
  it.each([
    ['2026-10-27T11:59:30Z', 'just now'],
    ['2026-10-27T11:55:00Z', '5 minutes ago'],
    ['2026-10-27T09:00:00Z', '3 hours ago'],
    ['2026-10-26T12:00:00Z', 'yesterday'],
    ['2026-10-13T12:00:00Z', '2 weeks ago'],
    ['2026-07-27T12:00:00Z', '3 months ago'],
    ['not a date', ''],
  ])('%s -> %s', (iso, text) => {
    expect(timeAgo(iso, now)).toBe(text)
  })
})

describe('topicAction', () => {
  it.each([
    [{ id: 'a', status: 'unlocked' }, {}, 'Start topic'],
    [{ id: 'a', status: 'in_progress' }, {}, 'Continue'],
    [{ id: 'a', status: 'in_progress' }, { retry: true }, 'Retry quiz'],
    [{ id: 'a', status: 'unlocked' }, { retry: true }, 'Retry quiz'],
    [{ id: 'a', status: 'completed' }, {}, 'Practise again'],
  ])('%j %j -> %s', (topic, options, label) => {
    expect(topicAction(topic, options)).toEqual({ label, to: '/quiz/a' })
  })

  it('encodes the topic id in the link', () => {
    expect(topicAction({ id: 'a b/c', status: 'unlocked' }).to).toBe('/quiz/a%20b%2Fc')
  })
})
