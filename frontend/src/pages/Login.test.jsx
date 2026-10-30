import { act, fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser, loginRequest } from '@/api/auth'
import api, { tokenStorage } from '@/api/client'
import { fetchCatalogue, fetchHome } from '@/api/domains'
import { fetchTopicGraph, fetchTopicMap } from '@/api/topics'
import { home } from '@/test/fixtures'
import { deferred, fakeServer, httpError, LEARNER, networkError } from '@/test/helpers'
import { fetchDashboard } from '@/api/progress'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchTopicGraph: vi.fn(), fetchTopicMap: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/domains', () => ({ fetchCatalogue: vi.fn(), fetchHome: vi.fn(), joinDomain: vi.fn() }))

const session = { access_token: 'jwt-login', token_type: 'bearer', user: LEARNER }
// The home page for a learner with domains, or without any yet.
const landing = (hasDomains) => (hasDomains ? home() : { domains: [], up_next: [], suggestions: [], recent_attempts: [] })

const emailInput = () => screen.getByLabelText('Email')
const passwordInput = () => screen.getByLabelText('Password')
const submit = () => screen.getByRole('button', { name: 'Log in' })

async function fillAndSubmit(user, email = 'puja@example.com', password = 'StrongPassword123') {
  if (email) await user.type(emailInput(), email)
  if (password) await user.type(passwordInput(), password)
  await user.click(submit())
}

beforeEach(() => {
  // The dashboard's own behaviour is tested in Dashboard.test.jsx; here it just stays loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  // The graph and catalogue pages are tested in their own files; here they just stay loading.
  fetchTopicGraph.mockReturnValue(new Promise(() => {}))
  fetchTopicMap.mockReturnValue(new Promise(() => {}))
  fetchCatalogue.mockReturnValue(new Promise(() => {}))
  fetchHome.mockResolvedValue(landing(true))
})

describe('form', () => {
  it('has labelled email and password fields with the right autocomplete hints', async () => {
    renderAt('/login')
    await screen.findByRole('form', { name: 'Log in' })
    expect(emailInput()).toHaveAttribute('type', 'email')
    expect(emailInput()).toHaveAttribute('autocomplete', 'email')
    expect(emailInput()).toHaveFocus()
    expect(passwordInput()).toHaveAttribute('type', 'password')
    expect(passwordInput()).toHaveAttribute('autocomplete', 'current-password')
  })

  it('checks the fields before sending anything, and focuses the first problem', async () => {
    const user = userEvent.setup()
    renderAt('/login')
    await user.click(await screen.findByRole('button', { name: 'Log in' }))
    expect(screen.getByText('Enter your email address')).toBeInTheDocument()
    expect(screen.getByText('Enter your password')).toBeInTheDocument()
    expect(emailInput()).toHaveAttribute('aria-invalid', 'true')
    expect(emailInput()).toHaveAccessibleDescription('Enter your email address')
    expect(emailInput()).toHaveFocus()
    expect(loginRequest).not.toHaveBeenCalled()
  })

  it('clears a message as soon as the field is fixed', async () => {
    const user = userEvent.setup()
    renderAt('/login')
    await user.type(await screen.findByLabelText('Email'), 'puja')
    await user.click(submit())
    expect(screen.getByText('Enter a valid email address, like name@example.com')).toBeInTheDocument()
    await user.type(emailInput(), '@example.com')
    expect(screen.queryByText(/valid email address/)).not.toBeInTheDocument()
    expect(emailInput()).not.toHaveAttribute('aria-invalid')
    // The untouched password error is still there.
    expect(screen.getByText('Enter your password')).toBeInTheDocument()
  })

  it('shows and hides the password', async () => {
    const user = userEvent.setup()
    renderAt('/login')
    await user.type(await screen.findByLabelText('Password'), 'secret123')
    const toggle = screen.getByRole('button', { name: 'Show password' })
    expect(toggle).toHaveAttribute('aria-pressed', 'false')
    await user.click(toggle)
    expect(passwordInput()).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Hide password' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Hide password' }))
    expect(passwordInput()).toHaveAttribute('type', 'password')
  })
})

describe('signing in', () => {
  // Email inputs drop surrounding spaces themselves (HTML value sanitisation); the page trims too.
  it('sends the trimmed email and the exact password, then opens the home page', async () => {
    loginRequest.mockResolvedValue(session)
    const user = userEvent.setup()
    const { router } = renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user, '  puja@example.com  ', ' pass word ')
    expect(loginRequest).toHaveBeenCalledWith({ email: 'puja@example.com', password: ' pass word ' })
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
    expect(router.state.location.pathname).toBe('/home')
    expect(tokenStorage.get()).toBe('jwt-login')
  })

  it('opens the catalogue for a learner who has not joined a domain yet', async () => {
    loginRequest.mockResolvedValue(session)
    fetchHome.mockResolvedValue(landing(false))
    const user = userEvent.setup()
    const { router } = renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user)
    await screen.findByRole('heading', { level: 1, name: 'Domains' })
    expect(router.state.location.pathname).toBe('/domains')
  })

  it('returns to the page the learner was sent away from', async () => {
    loginRequest.mockResolvedValue(session)
    const user = userEvent.setup()
    const { router } = renderAt('/map')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user)
    await screen.findByRole('heading', { name: 'Full map' })
    expect(router.state.location.pathname).toBe('/map')
  })

  it('shows progress and ignores extra clicks while signing in', async () => {
    const pending = deferred()
    loginRequest.mockReturnValue(pending.promise)
    const user = userEvent.setup()
    renderAt('/login')
    await screen.findByLabelText('Email')
    await user.type(emailInput(), 'puja@example.com')
    await user.type(passwordInput(), 'StrongPassword123')
    await user.click(submit())
    const busy = screen.getByRole('button', { name: 'Logging in…' })
    expect(busy).toBeDisabled()
    await user.click(busy)
    await user.keyboard('{Enter}')
    expect(loginRequest).toHaveBeenCalledTimes(1)
    await act(async () => pending.resolve(session))
    await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })
  })

  it('a second submit event fired before the page re-renders is ignored too', async () => {
    const pending = deferred()
    loginRequest.mockReturnValue(pending.promise)
    const user = userEvent.setup()
    renderAt('/login')
    await user.type(await screen.findByLabelText('Email'), 'puja@example.com')
    await user.type(passwordInput(), 'StrongPassword123')
    const form = screen.getByRole('form', { name: 'Log in' })
    fireEvent.submit(form)
    fireEvent.submit(form)
    expect(loginRequest).toHaveBeenCalledTimes(1)
    await act(async () => pending.resolve(session))
  })
})

describe('failures', () => {
  it('wrong email or password: a clear message, values kept, the form usable again', async () => {
    loginRequest.mockRejectedValue(httpError(401, 'Incorrect email or password'))
    const user = userEvent.setup()
    const { router } = renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user, 'puja@example.com', 'WrongPassword')
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
    expect(router.state.location.pathname).toBe('/login')
    expect(emailInput()).toHaveValue('puja@example.com')
    expect(passwordInput()).toHaveValue('WrongPassword')
    expect(submit()).toBeEnabled()
    expect(tokenStorage.get()).toBeNull()
  })

  it('server unreachable: says so', async () => {
    loginRequest.mockRejectedValue(networkError())
    const user = userEvent.setup()
    renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user)
    expect(await screen.findByRole('alert')).toHaveTextContent("Can't reach the AdaptLearn server")
  })

  it('server-side field errors appear next to the field', async () => {
    const error = httpError(422, 'email: value is not a valid email address')
    error.response.data.errors = [{ field: 'email', message: 'value is not a valid email address' }]
    loginRequest.mockRejectedValue(error)
    const user = userEvent.setup()
    renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user, 'puja@example.test')
    await waitFor(() => expect(emailInput()).toHaveAccessibleDescription('Value is not a valid email address'))
    expect(emailInput()).toHaveFocus()
  })

  it('a new attempt clears the previous message', async () => {
    loginRequest.mockRejectedValueOnce(httpError(401, 'Incorrect email or password'))
    const pending = deferred()
    loginRequest.mockReturnValueOnce(pending.promise)
    const user = userEvent.setup()
    renderAt('/login')
    await screen.findByLabelText('Email')
    await fillAndSubmit(user)
    await screen.findByRole('alert')
    await user.click(submit())
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    await act(async () => pending.resolve(session))
  })
})

it('after a session expires, the notice gives way to the error of a failed attempt', async () => {
  tokenStorage.set('jwt-old')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  const user = userEvent.setup()
  renderAt('/home')
  await screen.findByRole('heading', { name: 'Welcome back, Puja Sharma' })

  fakeServer(401, { detail: 'Could not validate credentials' })
  await act(() => api.get('/home').catch(() => {}))
  expect(await screen.findByRole('alert')).toHaveTextContent('Your session has expired')

  loginRequest.mockRejectedValue(httpError(401, 'Incorrect email or password'))
  await fillAndSubmit(user)
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Incorrect email or password'))
  expect(screen.queryByText('Your session has expired')).not.toBeInTheDocument()
})
