import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchHome, joinDomain } from '@/api/domains'
import { fetchDashboard } from '@/api/progress'
import { fetchActiveQuiz } from '@/api/quiz'
import { fetchTopicMap } from '@/api/topics'
import { domainSummary, home } from '@/test/fixtures'
import { deferred, httpError, LEARNER } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/quiz', () => ({ fetchActiveQuiz: vi.fn(), generateQuiz: vi.fn(), nextQuestion: vi.fn(), answerQuestion: vi.fn(), reportEvents: vi.fn(), submitQuiz: vi.fn() }))

beforeEach(() => {
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  // Pages reached from here are tested in their own files; here they just stay loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  fetchTopicMap.mockReturnValue(new Promise(() => {}))
  fetchActiveQuiz.mockReturnValue(new Promise(() => {}))
})

async function open(data = home()) {
  fetchHome.mockResolvedValue(data)
  const user = userEvent.setup()
  const view = renderAt('/home')
  await screen.findByRole('region', { name: 'Recent quizzes' })
  return { user, ...view }
}

const region = (name) => screen.getByRole('region', { name })
const card = (name) => screen.getByRole('article', { name })

/** A suggested domain: not joined, with a head start. */
const suggestion = (overrides = {}) =>
  domainSummary({
    id: 'data-science', name: 'Data Science', description: 'Analyse data with Python.', total_topics: 12,
    suggested: true, known_topics: [{ id: 'python_basics', name: 'Python Basics' }],
    ready_topics: [{ id: 'pandas', name: 'Pandas' }, { id: 'numpy', name: 'NumPy' }],
    ...overrides,
  })

describe('loading', () => {
  it('shows a skeleton until the home page arrives', async () => {
    const pending = deferred()
    fetchHome.mockReturnValue(pending.promise)
    renderAt('/home')
    expect(await screen.findByRole('status', { name: 'Loading your home page' })).toBeInTheDocument()
    await act(async () => pending.resolve(home()))
    expect(region('Your domains')).toBeInTheDocument()
  })

  it('offers a retry when it cannot be loaded', async () => {
    fetchHome.mockRejectedValueOnce(httpError(503, 'Database is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    renderAt('/home')
    expect(await screen.findByRole('heading', { name: "Couldn't load your home page" })).toBeInTheDocument()
    fetchHome.mockResolvedValueOnce(home())
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('region', { name: 'Your domains' })).toBeInTheDocument()
  })
})

describe('header', () => {
  it('greets the learner and names what they are learning', async () => {
    await open()
    expect(screen.getByRole('heading', { level: 1, name: 'Welcome back, Puja Sharma' })).toBeInTheDocument()
    expect(screen.getByText('Learning Foundations and Web Development')).toBeInTheDocument()
    expect(within(screen.getByRole('main')).getByRole('link', { name: 'Browse domains' })).toHaveAttribute('href', '/domains')
  })

  it('a learner with no domain is invited to choose one', async () => {
    fetchHome.mockResolvedValue({ domains: [], up_next: [], suggestions: [], recent_attempts: [] })
    renderAt('/home')
    expect(await screen.findByRole('heading', { name: 'Choose what to learn' })).toBeInTheDocument()
    expect(screen.getByText("You haven't joined a domain yet.")).toBeInTheDocument()
    const links = screen.getAllByRole('link', { name: 'Browse domains' })
    expect(links.map((a) => a.getAttribute('href'))).toEqual(['/domains', '/domains'])
    expect(screen.queryByRole('region', { name: 'Your domains' })).not.toBeInTheDocument()
  })
})

describe('your domains', () => {
  it('shows each joined domain with its progress and next topic', async () => {
    await open()
    const items = within(region('Your domains')).getAllByRole('article')
    expect(items.map((item) => within(item).getByRole('heading').textContent)).toEqual(['Foundations', 'Web Development'])
    const foundations = card('Foundations')
    expect(foundations).toHaveTextContent('1 of 3 topics completed')
    expect(within(foundations).getByRole('progressbar', { name: 'Progress' })).toHaveAttribute('aria-valuenow', '33')
    expect(foundations).toHaveTextContent('Next: Command Line')
    expect(within(foundations).getByRole('link', { name: 'Open dashboard: Foundations' })).toHaveAttribute(
      'href',
      '/domains/foundations',
    )
  })

  it('a domain not set up yet leads to its onboarding', async () => {
    const data = home()
    data.domains[1] = { ...data.domains[1], onboarded: false, up_next: null }
    await open(data)
    const web = card('Web Development')
    expect(web).toHaveTextContent('Tell us what you already know to get your path.')
    expect(within(web).getByRole('link', { name: 'Finish setting up Web Development' })).toHaveAttribute(
      'href',
      '/domains/web-development/onboarding',
    )
  })

  it.each([
    [{ curriculum_complete: true, up_next: null }, 'Every topic completed'],
    [{ up_next: null }, "Finish the topics you're working on to unlock the next ones."],
  ])('says what is next when there is no next topic (%#)', async (changes, text) => {
    const data = home()
    data.domains[0] = { ...data.domains[0], ...changes }
    await open(data)
    expect(card('Foundations')).toHaveTextContent(text)
  })
})

describe('up next', () => {
  it('shows the next topics across domains, with the domains each counts towards', async () => {
    await open()
    const items = within(region('Up next')).getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[1]).toHaveTextContent('Counts towards Foundations and Web Development')
    expect(items[0]).toHaveTextContent('Counts towards Foundations')
    // Git Basics: the latest quiz on it failed.
    expect(within(items[1]).getByRole('link', { name: 'Retry quiz: Git Basics' })).toHaveAttribute('href', '/quiz/git_basics')
    expect(within(items[0]).getByRole('link', { name: 'Start topic: Command Line' })).toHaveAttribute('href', '/quiz/command_line')
  })

  it('with a single domain, cards do not repeat which domain they count towards', async () => {
    const data = home()
    data.domains = [data.domains[0]]
    data.up_next = [data.up_next[0]]
    await open(data)
    expect(region('Up next')).not.toHaveTextContent('Counts towards')
  })

  it('a quiz opened from here leads back here', async () => {
    const { user, router } = await open()
    await user.click(screen.getByRole('link', { name: 'Start topic: Command Line' }))
    expect(router.state.location.pathname).toBe('/quiz/command_line')
    expect(router.state.location.state).toEqual({ from: '/home' })
  })

  it('asks to finish setting up when no domain has been set up', async () => {
    const data = home({ up_next: [] })
    data.domains = data.domains.map((d) => ({ ...d, onboarded: false, up_next: null }))
    await open(data)
    expect(region('Up next')).toHaveTextContent('Finish setting up to get your next topics')
    expect(region('Up next')).toHaveTextContent('Tell us what you already know in Foundations and Web Development')
  })

  it('celebrates when every joined domain is complete', async () => {
    const data = home({ up_next: [] })
    data.domains = data.domains.map((d) => ({ ...d, curriculum_complete: true, up_next: null }))
    await open(data)
    const next = region('Up next')
    expect(within(next).getByRole('heading', { name: "You've completed every domain you joined" })).toBeInTheDocument()
    expect(within(next).getByRole('link', { name: 'Browse domains' })).toHaveAttribute('href', '/domains')
  })

  it('otherwise says there is nothing to start right now', async () => {
    await open(home({ up_next: [] }))
    expect(region('Up next')).toHaveTextContent('Nothing to start right now')
  })
})

describe('suggestions', () => {
  it('is hidden when there is nothing to suggest', async () => {
    await open()
    expect(screen.queryByRole('region', { name: 'Suggested for you' })).not.toBeInTheDocument()
  })

  it('shows the head start in each suggested domain', async () => {
    await open(home({ suggestions: [suggestion()] }))
    const data = card('Data Science')
    expect(data).toHaveTextContent('Analyse data with Python.')
    expect(data).toHaveTextContent('Already completed: Python Basics')
    expect(data).toHaveTextContent('Ready to start: Pandas and NumPy')
  })

  it('joining a suggested domain opens its onboarding', async () => {
    joinDomain.mockResolvedValue({ domain: 'data-science', domain_name: 'Data Science', joined_at: '2026-10-31T00:00:00Z', onboarded: false })
    const { user, router } = await open(home({ suggestions: [suggestion()] }))
    await user.click(screen.getByRole('button', { name: 'Join Data Science' }))
    expect(joinDomain).toHaveBeenCalledWith('data-science')
    expect(router.state.location.pathname).toBe('/domains/data-science/onboarding')
  })

  it('a failed join says so on that domain and can be tried again', async () => {
    const pending = deferred()
    joinDomain.mockReturnValueOnce(pending.promise)
    const { user } = await open(home({ suggestions: [suggestion(), suggestion({ id: 'devops', name: 'DevOps' })] }))
    await user.click(screen.getByRole('button', { name: 'Join Data Science' }))
    // While one join is in flight, every Join button waits.
    expect(within(card('Data Science')).getByRole('button', { name: 'Join Data Science' })).toHaveTextContent('Joining…')
    expect(screen.getByRole('button', { name: 'Join DevOps' })).toBeDisabled()
    await act(async () => pending.reject(httpError(503, 'Database is temporarily unavailable. Please try again shortly.')))
    expect(within(card('Data Science')).getByRole('alert')).toHaveTextContent('Database is temporarily unavailable')
    expect(within(card('DevOps')).queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Join Data Science' })).toBeEnabled()
  })
})

describe('recent quizzes', () => {
  it('shows the latest quizzes from any domain', async () => {
    await open()
    const items = within(region('Recent quizzes')).getAllByRole('listitem')
    expect(items).toHaveLength(1)
    expect(items[0]).toHaveTextContent('Git Basics')
    expect(items[0]).toHaveTextContent('Needs retry')
  })
})
