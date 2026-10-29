import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { registerRequest } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchLearningPath, fetchTopicGraph } from '@/api/topics'
import { deferred, httpError, networkError } from '@/test/helpers'
import { fetchDashboard } from '@/api/progress'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchLearningPath: vi.fn(), fetchTopicGraph: vi.fn(), markKnownTopics: vi.fn() }))

const NEW_USER = { id: 12, username: 'New Learner', email: 'new@example.com' }
const session = { access_token: 'jwt-new', token_type: 'bearer', user: NEW_USER }

const field = (label) => screen.getByLabelText(label)
const submit = () => screen.getByRole('button', { name: 'Create account' })

async function fill(user, { username = 'New Learner', email = 'new@example.com', password = 'StrongPassword123', confirm = password } = {}) {
  if (username) await user.type(field('Username'), username)
  if (email) await user.type(field('Email'), email)
  if (password) await user.type(field('Password'), password)
  if (confirm) await user.type(field('Confirm password'), confirm)
}

async function open() {
  const user = userEvent.setup()
  const view = renderAt('/register')
  await screen.findByRole('form', { name: 'Create account' })
  return { user, ...view }
}

beforeEach(() => {
  // The dashboard's own behaviour is tested in Dashboard.test.jsx; here it just stays loading.
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  // The onboarding page's own behaviour is tested in Onboarding.test.jsx; here it just stays loading.
  fetchTopicGraph.mockReturnValue(new Promise(() => {}))
  fetchLearningPath.mockResolvedValue({ domain: 'Web Development', onboarded: false, curriculum_complete: false, recommended: [] })
})

describe('form', () => {
  it('has the four labelled fields with the right autocomplete hints', async () => {
    await open()
    expect(field('Username')).toHaveAttribute('autocomplete', 'nickname')
    expect(field('Username')).toHaveFocus()
    expect(field('Email')).toHaveAttribute('autocomplete', 'email')
    expect(field('Password')).toHaveAttribute('autocomplete', 'new-password')
    expect(field('Password')).toHaveAccessibleDescription('At least 8 characters.')
    expect(field('Confirm password')).toHaveAttribute('autocomplete', 'new-password')
  })

  it('reports every problem before sending anything', async () => {
    const { user } = await open()
    await user.click(submit())
    expect(screen.getByText('Enter a username')).toBeInTheDocument()
    expect(screen.getByText('Enter your email address')).toBeInTheDocument()
    expect(screen.getByText('Enter a password')).toBeInTheDocument()
    expect(screen.getByText('Re-enter your password')).toBeInTheDocument()
    expect(field('Username')).toHaveFocus()
    expect(registerRequest).not.toHaveBeenCalled()
  })

  it('applies the server’s password rules', async () => {
    const { user } = await open()
    await fill(user, { password: 'short' })
    await user.click(submit())
    expect(field('Password')).toHaveAccessibleDescription('Use at least 8 characters')
    expect(field('Password')).toHaveFocus()
    expect(registerRequest).not.toHaveBeenCalled()
  })

  it('catches mismatched passwords, and clears the message once they match', async () => {
    const { user } = await open()
    await fill(user, { password: 'StrongPassword123', confirm: 'StrongPassword12' })
    await user.click(submit())
    expect(field('Confirm password')).toHaveAccessibleDescription("Passwords don't match")
    expect(field('Confirm password')).toHaveFocus()
    await user.type(field('Confirm password'), '3')
    expect(screen.queryByText("Passwords don't match")).not.toBeInTheDocument()
  })

  it('each password field has its own show/hide toggle', async () => {
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Show confirm password' }))
    expect(field('Confirm password')).toHaveAttribute('type', 'text')
    expect(field('Password')).toHaveAttribute('type', 'password')
  })
})

describe('creating the account', () => {
  it('sends trimmed username and email with the exact password, then opens onboarding', async () => {
    registerRequest.mockResolvedValue(session)
    const { user, router } = await open()
    await fill(user, { username: '  New Learner ', email: ' new@example.com ', password: ' Strong Password ' })
    await user.click(submit())
    expect(registerRequest).toHaveBeenCalledWith({
      username: 'New Learner',
      email: 'new@example.com',
      password: ' Strong Password ',
    })
    await screen.findByRole('heading', { name: 'What do you already know?' })
    expect(router.state.location.pathname).toBe('/onboarding')
    expect(tokenStorage.get()).toBe('jwt-new')
    expect(screen.getByRole('button', { name: /account menu/ })).toHaveTextContent('New Learner')
  })

  it('ignores extra clicks while the account is being created', async () => {
    const pending = deferred()
    registerRequest.mockReturnValue(pending.promise)
    const { user } = await open()
    await fill(user)
    await user.click(submit())
    const busy = screen.getByRole('button', { name: 'Creating account…' })
    expect(busy).toBeDisabled()
    await user.click(busy)
    expect(registerRequest).toHaveBeenCalledTimes(1)
    await act(async () => pending.resolve(session))
    await screen.findByRole('heading', { name: 'What do you already know?' })
  })
})

describe('failures', () => {
  it('an email that is already registered is flagged on the email field', async () => {
    registerRequest.mockRejectedValue(httpError(409, 'An account with this email already exists'))
    const { user, router } = await open()
    await fill(user, { email: 'puja@example.com' })
    await user.click(submit())
    expect(await screen.findByText('An account with this email already exists')).toBeInTheDocument()
    expect(field('Email')).toHaveAttribute('aria-invalid', 'true')
    expect(field('Email')).toHaveFocus()
    expect(router.state.location.pathname).toBe('/register')
    expect(submit()).toBeEnabled()
  })

  it('server-side validation messages land on the matching field', async () => {
    const error = httpError(422, 'email: value is not a valid email address')
    error.response.data.errors = [{ field: 'email', message: 'value is not a valid email address' }]
    registerRequest.mockRejectedValue(error)
    const { user } = await open()
    await fill(user, { email: 'new@example.invalid' })
    await user.click(submit())
    expect(await screen.findByText('Value is not a valid email address')).toBeInTheDocument()
  })

  it.each([
    [networkError(), "Can't reach the AdaptLearn server"],
    [httpError(500, 'Something went wrong on our side. Please try again.'), 'Something went wrong on our side'],
  ])('other failures show a form-level message', async (error, message) => {
    registerRequest.mockRejectedValue(error)
    const { user } = await open()
    await fill(user)
    await user.click(submit())
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(tokenStorage.get()).toBeNull()
  })
})

it('a remembered page does not skip onboarding for a new account', async () => {
  registerRequest.mockResolvedValue(session)
  const user = userEvent.setup()
  const { router } = renderAt('/quiz/css_basics')
  await user.click(await screen.findByRole('link', { name: 'Create an account' }))
  await fill(user)
  await user.click(submit())
  await screen.findByRole('heading', { name: 'What do you already know?' })
  expect(router.state.location.pathname).toBe('/onboarding')
})
