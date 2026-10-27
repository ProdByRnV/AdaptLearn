import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser, loginRequest } from '@/api/auth'
import api, { tokenStorage } from '@/api/client'
import { fetchLearningPath, fetchTopicGraph } from '@/api/topics'
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
vi.mock('@/api/topics', () => ({ fetchLearningPath: vi.fn(), fetchTopicGraph: vi.fn(), markKnownTopics: vi.fn() }))
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
  // The onboarding page's own behaviour is tested in Onboarding.test.jsx; here it just stays loading.
  fetchTopicGraph.mockReturnValue(new Promise(() => {}))
  fetchLearningPath.mockResolvedValue({ domain: 'Web Development', onboarded: true, curriculum_complete: false, recommended: [] })
})

const PROTECTED = ['/', '/onboarding', '/dashboard', '/quiz/css_basics', '/graph']

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
    ['/dashboard', 'Welcome back, Puja Sharma'],
    ['/onboarding', 'What do you already know?'],
    ['/quiz/css_basics', 'Quiz'],
    ['/graph', 'Knowledge graph'],
  ])('%s renders inside the app shell', async (path, heading) => {
    signedIn()
    renderAt(path)
    expect(await screen.findByRole('heading', { level: 1, name: heading })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Account menu' })).toHaveTextContent('Puja Sharma')
  })

  it.each(['/', '/login', '/register'])('%s sends an onboarded learner to the dashboard', async (path) => {
    signedIn()
    const router = renderAt(path)
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it.each(['/', '/login', '/register'])('%s sends a learner who has not onboarded to onboarding', async (path) => {
    signedIn()
    fetchLearningPath.mockResolvedValue({ domain: 'Web Development', onboarded: false, curriculum_complete: false, recommended: [] })
    const router = renderAt(path)
    await screen.findByRole('heading', { name: 'What do you already know?' })
    expect(router.state.location.pathname).toBe('/onboarding')
  })

  it('falls back to the dashboard if the learning path cannot be loaded', async () => {
    signedIn()
    fetchLearningPath.mockRejectedValue(httpError(503, 'Curriculum service is temporarily unavailable.'))
    const router = renderAt('/')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it('shows a loader while deciding where to go', async () => {
    signedIn()
    const path = deferred()
    fetchLearningPath.mockReturnValue(path.promise)
    renderAt('/')
    expect(await screen.findByText('Getting things ready…', { selector: 'p' })).toBeInTheDocument()
    await act(async () => path.resolve({ onboarded: true }))
    expect(screen.getByRole('heading', { name: 'Welcome back, Puja Sharma' })).toBeInTheDocument()
  })

  it('returns to the remembered page after signing in, without asking for the learning path', async () => {
    signedIn()
    const router = renderAt({ pathname: '/login', state: { from: { pathname: '/quiz/css_basics', search: '' } } })
    await screen.findByRole('heading', { name: 'Quiz' })
    expect(router.state.location.pathname).toBe('/quiz/css_basics')
    expect(fetchLearningPath).not.toHaveBeenCalled()
  })

  it('marks the active nav link', async () => {
    signedIn()
    renderAt('/graph')
    await screen.findByRole('heading', { name: 'Knowledge graph' })
    expect(screen.getByRole('link', { name: 'Knowledge graph' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute('aria-current')
  })

  it('navigates with the navbar', async () => {
    signedIn()
    const user = userEvent.setup()
    const router = renderAt('/dashboard')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    const nav = screen.getByRole('navigation', { name: 'Main' })
    await user.click(within(nav).getByRole('link', { name: 'Knowledge graph' }))
    expect(router.state.location.pathname).toBe('/graph')
    expect(screen.getByRole('heading', { level: 1, name: 'Knowledge graph' })).toBeInTheDocument()
  })

  it('logs out from the account menu', async () => {
    signedIn()
    const user = userEvent.setup()
    const router = renderAt('/dashboard')
    await user.click(await screen.findByRole('button', { name: 'Account menu' }))
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
    const router = renderAt('/graph')
    await user.click(await screen.findByRole('button', { name: 'Account menu' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Log out' }))
    await screen.findByRole('heading', { name: 'Welcome back' })
    expect(router.state.location.state?.from).toBeUndefined()

    await user.type(screen.getByLabelText('Email'), 'someone@example.com')
    await user.type(screen.getByLabelText('Password'), 'StrongPassword123')
    await user.click(screen.getByRole('button', { name: 'Log in' }))
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it('logging out in another tab does not remember the page either', async () => {
    signedIn()
    const router = renderAt('/graph')
    await screen.findByRole('heading', { name: 'Knowledge graph' })
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
    renderAt('/dashboard')
    expect(screen.getByRole('status')).toHaveTextContent('Checking your session…')
    await act(async () => me.resolve(LEARNER))
    expect(screen.getByRole('heading', { name: 'Welcome back, Puja Sharma' })).toBeInTheDocument()
  })

  it('offers a retry when the server cannot be reached, without logging out', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockRejectedValueOnce(networkError())
    const user = userEvent.setup()
    const router = renderAt('/graph')
    expect(await screen.findByRole('heading', { name: "Couldn't restore your session" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/graph')
    expect(tokenStorage.get()).toBe('jwt-123')

    fetchCurrentUser.mockResolvedValueOnce(LEARNER)
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'Knowledge graph' })).toBeInTheDocument()
  })

  it('an expired session mid-use returns to login with an explanation', async () => {
    signedIn()
    const router = renderAt('/dashboard')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    fakeServer(401, { detail: 'Could not validate credentials' })
    await act(() => api.get('/progress/dashboard').catch(() => {}))
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(screen.getByRole('alert')).toHaveTextContent('Your session has expired')
    expect(router.state.location.state.from.pathname).toBe('/dashboard')
  })
})

describe('unknown pages', () => {
  it('signed out: 404 with a link to login', async () => {
    renderAt('/does-not-exist')
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Go to login' })).toHaveAttribute('href', '/login')
  })

  it('signed in: 404 with a link to the dashboard', async () => {
    signedIn()
    renderAt('/quiz')
    expect(await screen.findByRole('link', { name: 'Go to dashboard' })).toHaveAttribute('href', '/dashboard')
  })
})
