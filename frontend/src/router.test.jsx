import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import api, { tokenStorage } from '@/api/client'
import { AuthProvider } from '@/context/AuthProvider'
import { routes } from '@/router'
import { deferred, fakeServer, LEARNER, networkError } from '@/test/helpers'

vi.mock('@/api/auth', () => ({
  fetchCurrentUser: vi.fn(),
  loginRequest: vi.fn(),
  registerRequest: vi.fn(),
}))

function renderAt(entry) {
  const router = createMemoryRouter(routes, { initialEntries: [entry] })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return router
}

function signedIn(user = LEARNER) {
  tokenStorage.set('jwt-123')
  fetchCurrentUser.mockResolvedValue(user)
}

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

  it('/ goes to the dashboard', async () => {
    signedIn()
    const router = renderAt('/')
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it.each(['/login', '/register'])('%s sends a signed-in learner to the dashboard', async (path) => {
    signedIn()
    const router = renderAt(path)
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it('returns to the remembered page after signing in', async () => {
    signedIn()
    const router = renderAt({ pathname: '/login', state: { from: { pathname: '/quiz/css_basics', search: '' } } })
    await screen.findByRole('heading', { name: 'Quiz' })
    expect(router.state.location.pathname).toBe('/quiz/css_basics')
  })

  it('shows the quiz topic from the URL', async () => {
    signedIn()
    renderAt('/quiz/git_basics')
    expect(await screen.findByText('Topic: git_basics')).toBeInTheDocument()
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
    await user.click(screen.getByRole('link', { name: 'Knowledge graph' }))
    expect(router.state.location.pathname).toBe('/graph')
    expect(screen.getByRole('list', { name: 'Topic status legend' })).toHaveTextContent(
      'CompletedIn progressUnlockedLocked',
    )
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
