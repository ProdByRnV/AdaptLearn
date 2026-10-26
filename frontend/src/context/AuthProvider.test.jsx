import { act, render, renderHook, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser, loginRequest, registerRequest } from '@/api/auth'
import api, { tokenStorage } from '@/api/client'
import { AuthProvider } from '@/context/AuthProvider'
import { useAuth } from '@/hooks/useAuth'
import { deferred, fakeServer, httpError, LEARNER, networkError } from '@/test/helpers'

vi.mock('@/api/auth', () => ({
  fetchCurrentUser: vi.fn(),
  loginRequest: vi.fn(),
  registerRequest: vi.fn(),
}))

// The latest context value, so tests can call login()/logout() and inspect fields directly.
let auth
function Probe() {
  // oxlint-disable-next-line react/globals
  auth = useAuth()
  return (
    <dl>
      <dt>user</dt>
      <dd data-testid="user">{auth.user?.username ?? 'none'}</dd>
      <dt>state</dt>
      <dd data-testid="state">
        {auth.loading ? 'loading' : auth.isAuthenticated ? 'authenticated' : 'anonymous'}
      </dd>
    </dl>
  )
}

function renderProvider() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

const session = (user = LEARNER, token = 'jwt-123') => ({ access_token: token, token_type: 'bearer', user })

beforeEach(() => {
  auth = undefined
})

describe('restoring a session on load', () => {
  it('starts anonymous without a stored token and makes no request', () => {
    renderProvider()
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
    expect(fetchCurrentUser).not.toHaveBeenCalled()
  })

  it('loads the user for a stored token', async () => {
    tokenStorage.set('jwt-123')
    const me = deferred()
    fetchCurrentUser.mockReturnValue(me.promise)
    renderProvider()
    expect(screen.getByTestId('state')).toHaveTextContent('loading')
    await act(async () => me.resolve(LEARNER))
    expect(screen.getByTestId('state')).toHaveTextContent('authenticated')
    expect(screen.getByTestId('user')).toHaveTextContent('Puja Sharma')
    expect(auth.token).toBe('jwt-123')
  })

  it('drops a token the server rejects', async () => {
    tokenStorage.set('expired')
    fetchCurrentUser.mockRejectedValue(httpError(401, 'Could not validate credentials'))
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('anonymous'))
    expect(tokenStorage.get()).toBeNull()
    expect(auth.bootError).toBeNull()
  })

  it('keeps the token and offers a retry when the server is unreachable', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockRejectedValueOnce(networkError())
    renderProvider()
    await waitFor(() => expect(auth.bootError).toMatch(/can't reach/i))
    expect(tokenStorage.get()).toBe('jwt-123')
    expect(auth.isAuthenticated).toBe(false)

    fetchCurrentUser.mockResolvedValueOnce(LEARNER)
    await act(() => auth.refreshUser())
    expect(auth.bootError).toBeNull()
    expect(screen.getByTestId('state')).toHaveTextContent('authenticated')
  })
})

describe('login, register and logout', () => {
  it('login stores the token and the user', async () => {
    loginRequest.mockResolvedValue(session())
    renderProvider()
    await act(() => auth.login({ email: 'puja@example.com', password: 'StrongPassword123' }))
    expect(loginRequest).toHaveBeenCalledWith({ email: 'puja@example.com', password: 'StrongPassword123' })
    expect(tokenStorage.get()).toBe('jwt-123')
    expect(screen.getByTestId('state')).toHaveTextContent('authenticated')
  })

  it('register stores the token and the user', async () => {
    registerRequest.mockResolvedValue(session({ ...LEARNER, username: 'New Learner' }, 'jwt-new'))
    renderProvider()
    await act(() => auth.register({ username: 'New Learner', email: 'new@example.com', password: 'StrongPassword123' }))
    expect(tokenStorage.get()).toBe('jwt-new')
    expect(screen.getByTestId('user')).toHaveTextContent('New Learner')
  })

  it('a failed login rejects with the server error and stores nothing', async () => {
    loginRequest.mockRejectedValue(httpError(401, 'Incorrect email or password'))
    renderProvider()
    await expect(act(() => auth.login({ email: 'x@y.co', password: 'nope' }))).rejects.toMatchObject({
      response: { data: { detail: 'Incorrect email or password' } },
    })
    expect(tokenStorage.get()).toBeNull()
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
  })

  it('logout clears the token and the user', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('authenticated'))
    act(() => auth.logout())
    expect(tokenStorage.get()).toBeNull()
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
    expect(auth.sessionExpired).toBe(false)
  })

  it('ignores a /auth/me answer that arrives after logging out', async () => {
    tokenStorage.set('jwt-123')
    const me = deferred()
    fetchCurrentUser.mockReturnValue(me.promise)
    renderProvider()
    act(() => auth.logout())
    await act(async () => me.resolve(LEARNER))
    expect(screen.getByTestId('user')).toHaveTextContent('none')
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
  })
})

describe('session expiry', () => {
  it('any API call rejected with 401 logs the learner out and flags the expiry', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('authenticated'))

    fakeServer(401, { detail: 'Could not validate credentials' })
    await act(() => api.get('/progress/dashboard').catch(() => {}))
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
    expect(auth.sessionExpired).toBe(true)
    expect(tokenStorage.get()).toBeNull()

    // Logging in again clears the flag.
    loginRequest.mockResolvedValue(session())
    await act(() => auth.login({ email: 'puja@example.com', password: 'StrongPassword123' }))
    expect(auth.sessionExpired).toBe(false)
  })
})

describe('other tabs', () => {
  it('logging out in another tab logs this tab out', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('authenticated'))
    localStorage.removeItem('adaptlearn.token')
    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'adaptlearn.token', oldValue: 'jwt-123', newValue: null }))
    })
    expect(screen.getByTestId('state')).toHaveTextContent('anonymous')
  })

  it('logging in as someone else in another tab switches this tab to them', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockResolvedValueOnce(LEARNER)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Puja Sharma'))
    fetchCurrentUser.mockResolvedValueOnce({ id: 8, username: 'Ravi', email: 'ravi@example.com' })
    localStorage.setItem('adaptlearn.token', 'jwt-ravi')
    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'adaptlearn.token', oldValue: 'jwt-123', newValue: 'jwt-ravi' }))
    })
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ravi'))
    expect(auth.token).toBe('jwt-ravi')
  })

  it('ignores changes to unrelated storage keys', async () => {
    tokenStorage.set('jwt-123')
    fetchCurrentUser.mockResolvedValue(LEARNER)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('authenticated'))
    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'something-else', newValue: '1' }))
    })
    expect(fetchCurrentUser).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('state')).toHaveTextContent('authenticated')
  })
})

it('useAuth outside the provider explains the mistake', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used inside <AuthProvider>')
})
