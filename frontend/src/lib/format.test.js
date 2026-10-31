import { describe, expect, it } from 'vitest'

import { formatClock, formatPercent, splitQuizText, timeAgo } from '@/lib/format'
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

describe('formatClock', () => {
  it.each([
    [60, '1:00'],
    [65, '1:05'],
    [9, '0:09'],
    [0, '0:00'],
    [-3, '0:00'],
    [599.7, '9:59'],
    [undefined, '0:00'],
  ])('%s -> %s', (seconds, text) => {
    expect(formatClock(seconds)).toBe(text)
  })
})

describe('splitQuizText', () => {
  it('leaves plain text alone', () => {
    expect(splitQuizText('Which tag is a heading?')).toEqual([{ kind: 'text', value: 'Which tag is a heading?' }])
  })

  it('finds inline code', () => {
    expect(splitQuizText('Use `<h1>` for the `main` title')).toEqual([
      { kind: 'text', value: 'Use ' },
      { kind: 'code', value: '<h1>' },
      { kind: 'text', value: ' for the ' },
      { kind: 'code', value: 'main' },
      { kind: 'text', value: ' title' },
    ])
  })

  it('finds a fenced block and drops its language and edge line breaks', () => {
    expect(splitQuizText('What is logged?\n\n```javascript\nlet n = 1;\nconsole.log(n)\n```\nPick one.')).toEqual([
      { kind: 'text', value: 'What is logged?' },
      { kind: 'block', value: 'let n = 1;\nconsole.log(n)' },
      { kind: 'text', value: 'Pick one.' },
    ])
  })

  it('handles a block with no text around it, and inline code after it', () => {
    expect(splitQuizText('```\na()\n``` then `b`')).toEqual([
      { kind: 'block', value: 'a()' },
      { kind: 'text', value: ' then ' },
      { kind: 'code', value: 'b' },
    ])
  })

  it('keeps an unclosed backtick as text', () => {
    expect(splitQuizText('a ` b')).toEqual([{ kind: 'text', value: 'a ` b' }])
  })

  it('finds inline maths between \\( and \\)', () => {
    expect(splitQuizText('Solve \\( x^2 = 4 \\) for x.')).toEqual([
      { kind: 'text', value: 'Solve ' },
      { kind: 'maths', value: 'x^2 = 4' },
      { kind: 'text', value: ' for x.' },
    ])
  })

  it('finds a displayed formula between \\[ and \\], across lines, without the line breaks around it', () => {
    expect(splitQuizText('The area is\n\\[\nA = \\pi r^2\n\\]\nWhat is A when r = 2?')).toEqual([
      { kind: 'text', value: 'The area is' },
      { kind: 'mathsBlock', value: 'A = \\pi r^2' },
      { kind: 'text', value: 'What is A when r = 2?' },
    ])
    // ...including between a displayed formula and maths that follows it.
    expect(splitQuizText('\\[ a \\]\nthen \\( b \\)')).toEqual([
      { kind: 'mathsBlock', value: 'a' },
      { kind: 'text', value: 'then ' },
      { kind: 'maths', value: 'b' },
    ])
    // Line breaks around inline maths are the text's own and stay.
    expect(splitQuizText('First\n\\( x \\)\nnext')).toEqual([
      { kind: 'text', value: 'First\n' },
      { kind: 'maths', value: 'x' },
      { kind: 'text', value: '\nnext' },
    ])
  })

  it('reads maths and code in the same sentence', () => {
    expect(splitQuizText('`np.mean(x)` gives \\( \\bar{x} \\)')).toEqual([
      { kind: 'code', value: 'np.mean(x)' },
      { kind: 'text', value: ' gives ' },
      { kind: 'maths', value: '\\bar{x}' },
    ])
  })

  it('leaves maths delimiters inside code as code', () => {
    expect(splitQuizText('The regex `\\(\\d+\\)` matches')).toEqual([
      { kind: 'text', value: 'The regex ' },
      { kind: 'code', value: '\\(\\d+\\)' },
      { kind: 'text', value: ' matches' },
    ])
    expect(splitQuizText('```python\nre.compile(r"\\(x\\)")\n```')).toEqual([
      { kind: 'block', value: 're.compile(r"\\(x\\)")' },
    ])
  })

  it('keeps dollar amounts and unclosed delimiters as text', () => {
    expect(splitQuizText('It costs $5 and $10')).toEqual([{ kind: 'text', value: 'It costs $5 and $10' }])
    expect(splitQuizText('Open \\( but never closed')).toEqual([{ kind: 'text', value: 'Open \\( but never closed' }])
  })
})
