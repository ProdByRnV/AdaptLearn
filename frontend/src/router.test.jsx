import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser, loginRequest } from '@/api/auth'
import api, { tokenStorage } from '@/api/client'
import { fetchCatalogue, fetchHome } from '@/api/domains'
import { fetchTopicGraph, fetchTopicMap } from '@/api/topics'
import { home } from '@/test/fixtures'
import { deferred, fakeServer, httpError, LEARNER, networkError } from '@/test/helpers'
import { fetchDashboard } from '@/api/progress'
import { fetchActiveQuiz } from '@/api/quiz'
import { renderAt as mount } from '@/test/render-app'

vi.mock('@/api/auth', () => ({
  fetchCurrentUser: vi.fn(),
  loginRequest: vi.fn(),
  registerRequest: vi.fn(),
}))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))
vi.mock('@/api/quiz', () => ({ fetchActiveQuiz: vi.fn(), generateQuiz: vi.fn(), nextQuestion: vi.fn(), answerQuestion: vi.fn(), reportEvents: vi.fn(), submitQuiz: vi.fn() }))

const renderAt = (entry) => mount(entry).router

function signedIn(user = LEARNER) {
  tokenStorage.set('jwt-123')
  fetchCurrentUser.mockResolvedValue(user)
}

beforeEach(() => {
  // The dashboard's own behaviour is tested in Dashboard.test.jsx; here it just stays loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  // The quiz page's own behaviour is tested in QuizPage.test.jsx; here it just stays loading.
  fetchActiveQuiz.mockReturnValue(new Promise(() => {}))
  // The graph, map, onboarding and catalogue pages are tested in their own files; here they stay loading.
  fetchTopicGraph.mockReturnValue(new Promise(() => {}))
  fetchTopicMap.mockReturnValue(new Promise(() => {}))
  fetchCatalogue.mockReturnValue(new Promise(() => {}))
  // A learner with domains: signing in lands on the home page.
  fetchHome.mockResolvedValue(home())
})

const WEB = '/domains/web-development'
const NO_DOMAINS = { domains: [], up_next: [], suggestions: [], recent_attempts: [] }

const PROTECTED = ['/', '/home', '/domains', WEB, `${WEB}/graph`, `${WEB}/onboarding`, '/map', '/quiz/css_basics']

describe('signed out', () => {
  it.each(PROTECTED)('%s redirects to /login', async (path) => {
    const router = renderAt(path)
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
    expect(screen.queryByRole('navigation', { name: 'Main' })).not.toBeInTheDocument()
  })

  it('remembers the page the learner was going to', async () => {
    const router = renderAt('/quiz/css_basics?retry=1')
    await screen.findByRole('heading', { name: 'Welcome back' })
    expect(router.state.location.state.from).toMatchObject({ pathname: '/quiz/css_basics', search: '?retry=1' })
  })

  it.each([
    ['/login', 'Welcome back'],
    ['/register', 'Create your account'],
  ])('%s renders', async (path, heading) => {
    renderAt(path)
    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
  })

  it('links between login and register', async () => {
    const user = userEvent.setup()
    const router = renderAt('/login')
    await user.click(await screen.findByRole('link', { name: 'Create an account' }))
    expect(router.state.location.pathname).toBe('/register')
    await user.click(screen.getByRole('link', { name: 'Log in' }))
    expect(router.state.location.pathname).toBe('/login')
  })
})

describe('signed in', () => {
  it.each([
    ['/home', 'Welcome back, Puja Sharma'],
    ['/domains', 'Domains'],
    [WEB, 'Web Development'],
    [`${WEB}/graph`, 'Knowledge graph'],
    [`${WEB}/onboarding`, 'What do you already know?'],
    ['/map', 'Full map'],
    ['/quiz/css_basics', 'Quiz'],
  ])('%s renders inside the app shell', async (path, heading) => {
    signedIn()
    renderAt(path)
    expect(await screen.findByRole('heading', { level: 1, name: heading })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    // The visible name is part of the accessible name (WCAG 2.5.3), for voice control users.
    expect(screen.getByRole('button', { name: 'Puja Sharma account menu' })).toBeInTheDocument()
  })

  it.each(['/', '/login', '/register'])('%s sends a learner with a domain to their home page', async (path) => {
    signedIn()
    const router = renderAt(path)
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/home')
  })

  it.each(['/', '/login', '/register'])('%s sends a learner without a domain to the catalogue', async (path) => {
    signedIn()
    fetchHome.mockResolvedValue(NO_DOMAINS)
    const router = renderAt(path)
    await screen.findByRole('heading', { level: 1, name: 'Domains' })
    expect(router.state.location.pathname).toBe('/domains')
  })

  it('falls back to the home page if it cannot tell', async () => {
    signedIn()
    fetchHome.mockRejectedValue(httpError(503, 'Curriculum service is temporarily unavailable.'))
    const router = renderAt('/')
    await screen.findByRole('heading', { name: "Couldn't load your home page" })
    expect(router.state.location.pathname).toBe('/home')
  })

  it('shows a loader while deciding where to go', async () => {
    signedIn()
    const landing = deferred()
    fetchHome.mockReturnValueOnce(landing.promise)
    renderAt('/')
    expect(await screen.findByText('Getting things ready…', { selector: 'p' })).toBeInTheDocument()
    await act(async () => landing.resolve(home()))
    expect(await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })).toBeInTheDocument()
  })

  it('returns to the remembered page after signing in, without deciding where to land', async () => {
    signedIn()
    const router = renderAt({ pathname: '/login', state: { from: { pathname: '/quiz/css_basics', search: '' } } })
    await screen.findByRole('heading', { name: 'Quiz' })
    expect(router.state.location.pathname).toBe('/quiz/css_basics')
    expect(fetchHome).not.toHaveBeenCalled()
  })

  it.each([
    ['/home', 'Welcome back, Puja Sharma', 'Home'],
    ['/map', 'Full map', 'Full map'],
    ['/domains', 'Domains', 'Domains'],
    // A domain's own pages belong to Domains.
    [`${WEB}/graph`, 'Knowledge graph', 'Domains'],
  ])('marks the active nav link on %s', async (path, heading, active) => {
    signedIn()
    renderAt(path)
    await screen.findByRole('heading', { level: 1, name: heading })
    const nav = screen.getByRole('navigation', { name: 'Main' })
    const current = within(nav).getAllByRole('link').filter((a) => a.getAttribute('aria-current') === 'page')
    expect(current.map((a) => a.textContent)).toEqual([active])
  })

  it('navigates with the navbar, and the logo goes home', async () => {
    signedIn()
    const user = userEvent.setup()
    const router = renderAt('/home')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    const nav = screen.getByRole('navigation', { name: 'Main' })
    await user.click(within(nav).getByRole('link', { name: 'Full map' }))
    expect(router.state.location.pathname).toBe('/map')
    expect(screen.getByRole('heading', { level: 1, name: 'Full map' })).toBeInTheDocument()
    await user.click(within(nav).getByRole('link', { name: 'Domains' }))
    expect(router.state.location.pathname).toBe('/domains')
    await user.click(screen.getByRole('link', { name: 'AdaptLearn home' }))
    expect(router.state.location.pathname).toBe('/home')
  })

  it.each([
    ['/dashboard', '/home'],
    ['/onboarding', '/domains'],
    ['/graph?topic=css_basics', '/map?topic=css_basics'],
  ])('the old address %s now opens %s', async (from, to) => {
    signedIn()
    const router = renderAt(from)
    await waitFor(() => expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(to))
  })

  it('logs out from the account menu', async () => {
    signedIn()
    const user = userEvent.setup()
    const router = renderAt('/home')
    await user.click(await screen.findByRole('button', { name: /account menu/ }))
    expect(await screen.findByText('puja@example.com')).toBeInTheDocument()
    await user.click(screen.getByRole('menuitem', { name: 'Log out' }))
    await screen.findByRole('heading', { name: 'Welcome back' })
    expect(router.state.location.pathname).toBe('/login')
    expect(tokenStorage.get()).toBeNull()
    expect(screen.queryByText(/session has expired/i)).not.toBeInTheDocument()
  })

  it('logging out does not remember the page, so the next login starts fresh', async () => {
    signedIn()
    loginRequest.mockResolvedValue({ access_token: 'jwt-2', token_type: 'bearer', user: LEARNER })
    const user = userEvent.setup()
    const router = renderAt('/map')
    await user.click(await screen.findByRole('button', { name: /account menu/ }))
    await user.click(await screen.findByRole('menuitem', { name: 'Log out' }))
    await screen.findByRole('heading', { name: 'Welcome back' })
    expect(router.state.location.state?.from).toBeUndefined()

    await user.type(screen.getByLabelText('Email'), 'someone@example.com')
    await user.type(screen.getByLabelText('Password'), 'StrongPassword123')
    await user.click(screen.getByRole('button', { name: 'Log in' }))
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/home')
  })

  it('logging out in another tab does not remember the page either', async () => {
    signedIn()
    const router = renderAt('/map')
    await screen.findByRole('heading', { name: 'Full map' })
    localStorage.removeItem('adaptlearn.token')
    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'adaptlearn.token', oldValue: 'jwt-123', newValue: null }))
    })
    await screen.findByRole('heading', { name: 'Welcome back' })
    expect(router.state.location.state?.from).toBeUndefined()
  })
})

describe('checking the session', () => {
  it('shows a loader until /auth/me answers, then the page', async () => {
    tokenStorage.set('jwt-123')
    const me = deferred()
    fetchCurrentUser.mockReturnValue(me.promise)
    renderAt('/home')
    expect(screen.getByRole('status')).toHaveTextContent('Checking your session…')
    await act(async () => me.resolve(LEARNER))
    expect(screen.getByRole('heading', { name: 'Welcome back, Puja Sharma' })).toBeInTheDocument()
  })

  it('offers a retry when the server cannot be reached, without logging out', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockRejectedValueOnce(networkError())
    const user = userEvent.setup()
    const router = renderAt('/map')
    expect(await screen.findByRole('heading', { name: "Couldn't restore your session" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/map')
    expect(tokenStorage.get()).toBe('jwt-123')

    fetchCurrentUser.mockResolvedValueOnce(LEARNER)
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'Full map' })).toBeInTheDocument()
  })

  it('the startup error page is branded and offers a way to log out', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockRejectedValueOnce(httpError(503, 'Database is temporarily unavailable. Please try again shortly.'))
    const user = userEvent.setup()
    const router = renderAt('/home')
    expect(await screen.findByRole('heading', { level: 1, name: "Couldn't restore your session" })).toBeInTheDocument()
    expect(screen.getByText('Database is temporarily unavailable. Please try again shortly.')).toBeInTheDocument()
    expect(screen.getByText('AdaptLearn')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Log out' }))
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
    expect(router.state.location.state).toBeNull()
    expect(tokenStorage.get()).toBeNull()
  })

  it('an expired session mid-use returns to login with an explanation', async () => {
    signedIn()
    const router = renderAt('/home')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    fakeServer(401, { detail: 'Could not validate credentials' })
    await act(() => api.get('/home').catch(() => {}))
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(screen.getByRole('alert')).toHaveTextContent('Your session has expired')
    expect(router.state.location.state.from.pathname).toBe('/home')
  })
})

describe('unknown pages', () => {
  it('signed out: 404 with a link to login', async () => {
    renderAt('/does-not-exist')
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
    expect(screen.getByRole('main')).toContainElement(screen.getByRole('heading', { name: 'Page not found' }))
    expect(screen.getByRole('link', { name: 'Go to login' })).toHaveAttribute('href', '/login')
  })

  it('signed in: 404 with a link to the home page', async () => {
    signedIn()
    renderAt('/quiz')
    expect(await screen.findByRole('link', { name: 'Go to home' })).toHaveAttribute('href', '/home')
  })
})
