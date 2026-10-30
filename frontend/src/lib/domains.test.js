import { describe, expect, it } from 'vitest'

import { backLink, domainPath, isUnknownDomain, quizLinkState, topicInDomain } from '@/lib/domains'
import { httpError } from '@/test/helpers'

describe('domain paths', () => {
  it("builds each of a domain's pages", () => {
    expect(domainPath('web-development')).toBe('/domains/web-development')
    expect(domainPath('web-development', 'graph')).toBe('/domains/web-development/graph')
    expect(domainPath('web-development', 'onboarding')).toBe('/domains/web-development/onboarding')
    expect(topicInDomain('foundations', 'git_basics')).toBe('/domains/foundations/graph?topic=git_basics')
  })

  it('escapes what it puts in the URL', () => {
    expect(domainPath('a/b')).toBe('/domains/a%2Fb')
    expect(topicInDomain('x', 'a&b')).toBe('/domains/x/graph?topic=a%26b')
  })
})

describe('the way back from a quiz', () => {
  it('remembers the page a quiz was opened from, with its query', () => {
    expect(quizLinkState({ pathname: '/domains/web-development/graph', search: '?topic=html_basics' })).toEqual({
      from: '/domains/web-development/graph?topic=html_basics',
    })
  })

  it('a link on the quiz page keeps the original page', () => {
    expect(quizLinkState({ pathname: '/quiz/html_basics', search: '', state: { from: '/home' } })).toEqual({ from: '/home' })
    expect(quizLinkState({ pathname: '/quiz/html_basics', search: '', state: null })).toBeUndefined()
  })

  it.each([
    ['/domains/web-development', { to: '/domains/web-development', label: 'Back to dashboard' }],
    ['/domains/web-development/graph?topic=x', { to: '/domains/web-development/graph?topic=x', label: 'Back to the knowledge graph' }],
    ['/map', { to: '/map', label: 'Back to the knowledge graph' }],
    ['/home', { to: '/home', label: 'Back to home' }],
    ['/domains', { to: '/home', label: 'Back to home' }],
    ['https://example.com/domains/x', { to: '/home', label: 'Back to home' }],
    [undefined, { to: '/home', label: 'Back to home' }],
    [{ pathname: '/map' }, { to: '/home', label: 'Back to home' }],
  ])('from %s', (from, expected) => {
    expect(backLink(from)).toEqual(expected)
  })
})

it('recognises an unknown domain', () => {
  expect(isUnknownDomain(httpError(404, "Unknown domain 'x'"))).toBe(true)
  expect(isUnknownDomain(httpError(503))).toBe(false)
  expect(isUnknownDomain(null)).toBe(false)
})
