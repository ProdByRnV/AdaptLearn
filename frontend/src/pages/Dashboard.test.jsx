import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchCatalogue } from '@/api/domains'
import { fetchDashboard } from '@/api/progress'
import { catalogue, dashboard } from '@/test/fixtures'
import { deferred, httpError, LEARNER } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))

// The domain switcher reads the catalogue.
beforeEach(() => {
  fetchCatalogue.mockResolvedValue(catalogue())
})

async function open(data = dashboard(), entry = '/domains/web-development') {
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  fetchDashboard.mockResolvedValue(data)
  const user = userEvent.setup()
  const view = renderAt(entry)
  await screen.findByRole('region', { name: 'Your progress' })
  return { user, ...view }
}

const region = (name) => screen.getByRole('region', { name })
const stat = (label) => screen.getByRole('heading', { level: 3, name: label }).closest('[data-slot="card"]')

describe('loading', () => {
  it('shows a skeleton until the dashboard arrives', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    const pending = deferred()
    fetchDashboard.mockReturnValue(pending.promise)
    renderAt('/domains/web-development')
    expect(await screen.findByRole('status', { name: 'Loading your dashboard' })).toBeInTheDocument()
    await act(async () => pending.resolve(dashboard()))
    expect(screen.queryByRole('status', { name: 'Loading your dashboard' })).not.toBeInTheDocument()
    expect(region('Your progress')).toBeInTheDocument()
  })

  it('offers a retry when the dashboard cannot be loaded', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    fetchDashboard.mockRejectedValueOnce(httpError(503, 'Database is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    renderAt('/domains/web-development')
    expect(await screen.findByRole('heading', { name: "Couldn't load your dashboard" })).toBeInTheDocument()
    expect(screen.getByText('Database is temporarily unavailable. Please try again shortly.')).toBeInTheDocument()
    fetchDashboard.mockResolvedValueOnce(dashboard())
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('region', { name: 'Your progress' })).toBeInTheDocument()
  })
})

describe('header and stats', () => {
  it('names the domain from the URL and summarises progress in it', async () => {
    await open()
    expect(fetchDashboard).toHaveBeenCalledWith('web-development')
    expect(screen.getByRole('heading', { level: 1, name: 'Web Development' })).toBeInTheDocument()
    expect(screen.getByText('7 of 30 topics completed')).toBeInTheDocument()
    expect(within(screen.getByRole('main')).getByRole('link', { name: 'Knowledge graph' })).toHaveAttribute(
      'href',
      '/domains/web-development/graph',
    )
  })

  // Exit gate: no hard-coded numbers. Two different learners must produce different screens.
  it.each([
    [
      { total_topics: 30, completed_topics: 7, in_progress_topics: 2, mastered_topics: 5, average_mastery: 41.26, total_attempts: 6, flagged_attempts: 1, progress_percent: 23.3 },
      { progress: ['23%', '7 of 30 topics'], completed: ['7', '2 in progress'], mastered: '5', average: '41%', attempts: ['6', "1 flagged, didn't count"] },
    ],
    [
      { total_topics: 30, completed_topics: 0, in_progress_topics: 0, mastered_topics: 0, average_mastery: 10, total_attempts: 0, flagged_attempts: 0, progress_percent: 0 },
      { progress: ['0%', '0 of 30 topics'], completed: ['0', '0 in progress'], mastered: '0', average: '10%', attempts: ['0', 'All proctored'] },
    ],
    [
      { total_topics: 30, completed_topics: 30, in_progress_topics: 0, mastered_topics: 28, average_mastery: 97.84, total_attempts: 41, flagged_attempts: 3, progress_percent: 100 },
      { progress: ['100%', '30 of 30 topics'], completed: ['30', '0 in progress'], mastered: '28', average: '98%', attempts: ['41', "3 flagged, didn't count"] },
    ],
  ])('stat cards show the API numbers (%#)', async (stats, shown) => {
    await open(dashboard({ stats }))
    for (const text of shown.progress) expect(stat('Overall progress')).toHaveTextContent(text)
    expect(within(stat('Overall progress')).getByRole('progressbar', { name: 'Overall progress' })).toHaveAttribute(
      'aria-valuenow',
      String(Math.round(stats.progress_percent)),
    )
    for (const text of shown.completed) expect(stat('Completed')).toHaveTextContent(text)
    expect(stat('Mastered')).toHaveTextContent(shown.mastered)
    expect(stat('Average mastery')).toHaveTextContent(shown.average)
    for (const text of shown.attempts) expect(stat('Quiz attempts')).toHaveTextContent(text)
  })
})

describe('up next', () => {
  it('shows each recommended topic with everything the PRD asks for', async () => {
    await open()
    const cards = within(region('Up next')).getAllByRole('listitem')
    expect(cards).toHaveLength(3)
    const router = within(cards[2])
    expect(router.getByRole('heading', { name: 'React Router' })).toBeInTheDocument()
    expect(router.getByText('Client-side routing in React apps.')).toBeInTheDocument()
    expect(router.getByText('Advanced')).toBeInTheDocument()
    expect(router.getByText('Unlocked')).toBeInTheDocument()
    expect(router.getByRole('progressbar', { name: 'Mastery' })).toHaveAttribute('aria-valuenow', '10')
    expect(router.getByText('10%')).toBeInTheDocument()
    expect(router.getByText('Builds on React Fundamentals and ES Modules')).toBeInTheDocument()
    expect(within(cards[0]).getByText('No prerequisites')).toBeInTheDocument()
  })

  it('picks Start topic / Continue / Retry quiz and links to the quiz', async () => {
    await open()
    // SQL Basics: in progress, latest attempt failed -> Retry quiz.
    expect(within(region('Up next')).getByRole('link', { name: 'Retry quiz: SQL Basics' })).toHaveAttribute('href', '/quiz/sql_basics')
    // CSS Grid: in progress, latest attempt passed -> Continue.
    expect(screen.getByRole('link', { name: 'Continue: CSS Grid' })).toHaveAttribute('href', '/quiz/css_grid')
    // React Router: unlocked -> Start topic.
    expect(screen.getByRole('link', { name: 'Start topic: React Router' })).toHaveAttribute('href', '/quiz/react_router')
  })

  it('Retry quiz when the latest counted attempt failed, even if the topic does not need attention', async () => {
    const data = dashboard({ needs_attention: [] })
    data.recent_attempts = [
      { ...data.recent_attempts[1], id: 98, topic_id: 'css_grid', topic_name: 'CSS Grid', passed: false, score: 1 },
      ...data.recent_attempts,
    ]
    await open(data)
    expect(screen.getByRole('link', { name: 'Retry quiz: CSS Grid' })).toBeInTheDocument()
  })

  it('Retry quiz when the topic needs attention, even without a recent failed attempt', async () => {
    await open(dashboard({ recent_attempts: [] }))
    expect(within(region('Up next')).getByRole('link', { name: 'Retry quiz: SQL Basics' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Continue: CSS Grid' })).toBeInTheDocument()
  })

  it('a flagged attempt does not decide the action (it did not count)', async () => {
    const data = dashboard()
    data.recent_attempts = [
      { ...data.recent_attempts[1], id: 99, topic_id: 'css_grid', topic_name: 'CSS Grid', counted: false, passed: false },
      ...data.recent_attempts,
    ]
    await open(data)
    expect(screen.getByRole('link', { name: 'Continue: CSS Grid' })).toBeInTheDocument()
  })

  it('shows the curriculum-complete state instead of recommendations', async () => {
    await open(dashboard({ curriculum_complete: true, recommended: [] }))
    const next = region('Up next')
    expect(within(next).getByRole('heading', { name: "You've completed the Web Development curriculum" })).toBeInTheDocument()
    expect(within(next).getByRole('link', { name: 'Open the knowledge graph' })).toHaveAttribute('href', '/domains/web-development/graph')
    expect(within(next).getByRole('link', { name: 'Browse domains' })).toHaveAttribute('href', '/domains')
    expect(within(next).queryByRole('listitem')).not.toBeInTheDocument()
  })

  it('says so if there is nothing to start right now', async () => {
    await open(dashboard({ recommended: [] }))
    expect(within(region('Up next')).getByText('Nothing to start right now')).toBeInTheDocument()
  })
})

describe('needs attention', () => {
  it('lists struggling topics with their resources first, then a retry', async () => {
    await open()
    const attention = region('Needs attention')
    expect(within(attention).getByText('46% mastery after 3 attempts')).toBeInTheDocument()
    expect(within(attention).getByText('Review these before trying again:')).toBeInTheDocument()
    const link = within(attention).getByRole('link', { name: /SQLBolt lessons/ })
    expect(link).toHaveAttribute('href', 'https://sqlbolt.com/')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    expect(link).toHaveAccessibleName('SQLBolt lessons (Article, opens in a new tab)')
    expect(within(attention).getByRole('link', { name: /PostgreSQL tutorial \(Docs/ })).toBeInTheDocument()
    expect(within(attention).getByRole('link', { name: 'Retry quiz: SQL Basics' })).toHaveAttribute('href', '/quiz/sql_basics')
  })

  it('is hidden when nothing needs attention', async () => {
    await open(dashboard({ needs_attention: [] }))
    expect(screen.queryByRole('region', { name: 'Needs attention' })).not.toBeInTheDocument()
  })
})

describe('recent quizzes', () => {
  it('shows score, result, mastery change and when', async () => {
    await open()
    const items = within(region('Recent quizzes')).getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[1]).toHaveTextContent('SQL Basics')
    expect(items[1]).toHaveTextContent('1/3')
    expect(items[1]).toHaveTextContent('Needs retry')
    expect(items[1]).toHaveTextContent('Mastery46%to46%')
    expect(items[1]).toHaveTextContent('5 minutes ago')
    expect(items[2]).toHaveTextContent('Passed')
    expect(items[2]).toHaveTextContent('Mastery10%to99%')
    expect(items[2]).toHaveTextContent('3 hours ago')
  })

  it('marks a flagged attempt as not counted and shows no mastery change', async () => {
    await open()
    const flagged = within(region('Recent quizzes')).getAllByRole('listitem')[0]
    expect(flagged).toHaveTextContent('Git Basics')
    expect(flagged).toHaveTextContent('3/3')
    expect(flagged).toHaveTextContent("Flagged, didn't count")
    expect(within(flagged).getByText("Flagged, didn't count")).toHaveAttribute('title', 'Integrity score 75')
    expect(flagged).not.toHaveTextContent('Passed')
    expect(flagged).not.toHaveTextContent('Mastery')
  })

  it('has an empty state before the first quiz', async () => {
    await open(dashboard({ recent_attempts: [] }))
    expect(within(region('Recent quizzes')).getByText('No quizzes yet')).toBeInTheDocument()
  })
})

describe('mastery overview', () => {
  it('shows reachable topics, with locked ones one click away', async () => {
    const { user } = await open()
    const mastery = region('Mastery')
    const bars = () => within(mastery).getAllByRole('progressbar')
    expect(bars().map((b) => b.getAttribute('aria-valuenow'))).toEqual(['99', '46', '10'])
    expect(within(mastery).getByRole('progressbar', { name: 'HTML Basics' })).toBeInTheDocument()
    expect(within(mastery).queryByText('Testing Basics')).not.toBeInTheDocument()

    const toggle = within(mastery).getByRole('button', { name: 'Show 2 locked topics' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await user.click(toggle)
    expect(bars()).toHaveLength(5)
    expect(within(mastery).getByText('Testing Basics')).toBeInTheDocument()
    await user.click(within(mastery).getByRole('button', { name: 'Hide locked topics' }))
    expect(bars()).toHaveLength(3)
  })

  it('names each topic’s status for screen readers', async () => {
    await open()
    expect(within(region('Mastery')).getByText('(Completed)')).toHaveClass('sr-only')
  })
})

describe('onboarding', () => {
  it('prompts a learner who has not set up this domain', async () => {
    await open(dashboard({ onboarded: false }))
    expect(screen.getByRole('heading', { name: 'Already know some of this?' })).toBeInTheDocument()
    expect(screen.getByText(/Tell us which Web Development topics you're comfortable with/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Choose known topics' })).toHaveAttribute('href', '/domains/web-development/onboarding')
  })

  it('no prompt once onboarded', async () => {
    await open()
    expect(screen.queryByRole('heading', { name: 'Already know some of this?' })).not.toBeInTheDocument()
  })

  it('keeps the confirmation after onboarding alongside real data', async () => {
    await open(dashboard(), { pathname: '/domains/web-development', state: { onboarding: { knownCount: 4, addedPrerequisites: ['HTML Basics'] } } })
    expect(screen.getByText("You're all set")).toBeInTheDocument()
    expect(screen.getByText(/4 topics are marked as known/)).toBeInTheDocument()
    expect(region('Up next')).toBeInTheDocument()
  })
})

describe('domains', () => {
  it('switches between joined domains from the header, keeping the dashboard view', async () => {
    const { user, router } = await open()
    const switcher = screen.getByRole('button', { name: 'Web Development: switch domain' })
    await user.click(switcher)
    const menu = await screen.findByRole('menu')
    // Joined domains, plus the current one (not joined here), each with its progress.
    const items = within(menu).getAllByRole('menuitem')
    expect(items.map((item) => item.textContent)).toEqual(['Foundations33%', 'Web Development3%', 'Browse all domains'])
    expect(items[1]).toHaveAttribute('aria-current', 'page')
    expect(items[0]).toHaveAttribute('href', '/domains/foundations')
    expect(items[2]).toHaveAttribute('href', '/domains')

    fetchDashboard.mockResolvedValue(dashboard({ domain: 'foundations', domain_name: 'Foundations' }))
    await user.click(items[0])
    expect(router.state.location.pathname).toBe('/domains/foundations')
    expect(await screen.findByRole('heading', { level: 1, name: 'Foundations' })).toBeInTheDocument()
    expect(fetchDashboard).toHaveBeenLastCalledWith('foundations')
  })

  it("shows the next domain's loading state rather than the previous domain's data", async () => {
    const { user } = await open()
    const pending = deferred()
    fetchDashboard.mockReturnValue(pending.promise)
    await user.click(screen.getByRole('button', { name: 'Web Development: switch domain' }))
    await user.click(await screen.findByRole('menuitem', { name: /Foundations/ }))
    expect(await screen.findByRole('status', { name: 'Loading your dashboard' })).toBeInTheDocument()
    expect(screen.queryByText('7 of 30 topics completed')).not.toBeInTheDocument()
    await act(async () => pending.resolve(dashboard({ domain: 'foundations', domain_name: 'Foundations' })))
    expect(screen.getByRole('heading', { level: 1, name: 'Foundations' })).toBeInTheDocument()
  })

  it('the switcher says when the domains cannot be loaded, and still links to the catalogue', async () => {
    fetchCatalogue.mockRejectedValue(httpError(503))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Web Development: switch domain' }))
    expect(await screen.findByRole('menuitem', { name: "Couldn't load your domains" })).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByRole('menuitem', { name: 'Browse all domains' })).toHaveAttribute('href', '/domains')
  })

  it('an unknown domain says so and links to the catalogue', async () => {
    tokenStorage.set('jwt')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    fetchDashboard.mockRejectedValue(httpError(404, "Unknown domain 'underwater-basket-weaving'"))
    renderAt('/domains/underwater-basket-weaving')
    expect(await screen.findByRole('heading', { level: 1, name: "We couldn't find that domain" })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Browse domains' })).toHaveAttribute('href', '/domains')
    expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument()
  })
})
