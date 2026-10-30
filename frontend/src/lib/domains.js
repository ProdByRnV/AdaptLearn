// Where things live in the app now that there are several domains, and the way back from a quiz.

const VIEWS = { dashboard: '', graph: '/graph', onboarding: '/onboarding' }

/** A domain's page: its dashboard (default), knowledge graph or onboarding. */
export function domainPath(domainId, view = 'dashboard') {
  return `/domains/${encodeURIComponent(domainId)}${VIEWS[view]}`
}

/** A topic opened in a domain's knowledge graph. */
export function topicInDomain(domainId, topicId) {
  return `${domainPath(domainId, 'graph')}?topic=${encodeURIComponent(topicId)}`
}

/**
 * Router state for a link to a quiz: remember the page it was opened from, so the quiz can lead
 * back there. Links on the quiz page itself (retry, next topics) keep the original page.
 */
export function quizLinkState({ pathname, search = '', state }) {
  if (pathname.startsWith('/quiz/')) return state ?? undefined
  return { from: `${pathname}${search}` }
}

/** The quiz's way back: to the dashboard or graph it was opened from, otherwise home. */
export function backLink(from) {
  const path = typeof from === 'string' ? from.split(/[?#]/)[0] : ''
  if (path === '/map' || /^\/domains\/[^/]+\/graph$/.test(path)) return { to: from, label: 'Back to the knowledge graph' }
  if (/^\/domains\/[^/]+$/.test(path)) return { to: from, label: 'Back to dashboard' }
  return { to: '/home', label: 'Back to home' }
}

/** True when the API said the domain doesn't exist. */
export function isUnknownDomain(error) {
  return error?.response?.status === 404
}
