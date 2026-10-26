import { describe, expect, it, vi } from 'vitest'

import api, { API_URL, getErrorMessage, getRetryAfterSeconds, setUnauthorizedHandler, tokenStorage } from '@/api/client'
import { fakeServer, httpError, networkError } from '@/test/helpers'

describe('request interceptor', () => {
  it('attaches the stored token as a Bearer header', async () => {
    tokenStorage.set('abc.def.ghi')
    const server = fakeServer(200)
    await api.get('/auth/me')
    expect(server.mock.calls[0][0].headers.get('Authorization')).toBe('Bearer abc.def.ghi')
  })

  it('sends no Authorization header without a token', async () => {
    const server = fakeServer(200)
    await api.post('/auth/login', { email: 'a@b.co', password: 'x' })
    expect(server.mock.calls[0][0].headers.has('Authorization')).toBe(false)
  })

  it('uses the API base URL and a 15 second timeout', async () => {
    const server = fakeServer(200)
    await api.get('/health')
    const config = server.mock.calls[0][0]
    expect(config.baseURL).toBe(API_URL)
    expect(config.timeout).toBe(15_000)
    expect(API_URL).not.toMatch(/\/$/)
  })
})

describe('401 handling', () => {
  it('ends the session when the current token is rejected', async () => {
    const handler = vi.fn()
    const unsubscribe = setUnauthorizedHandler(handler)
    tokenStorage.set('expired')
    fakeServer(401, { detail: 'Could not validate credentials' })
    await expect(api.get('/auth/me')).rejects.toMatchObject({ response: { status: 401 } })
    expect(handler).toHaveBeenCalledTimes(1)
    unsubscribe()
  })

  it('leaves a 401 without a token (e.g. wrong password) to the caller', async () => {
    const handler = vi.fn()
    const unsubscribe = setUnauthorizedHandler(handler)
    fakeServer(401, { detail: 'Incorrect email or password' })
    await expect(api.post('/auth/login', {})).rejects.toBeTruthy()
    expect(handler).not.toHaveBeenCalled()
    unsubscribe()
  })

  it('ignores a 401 for a token that was replaced while the request was in flight', async () => {
    const handler = vi.fn()
    const unsubscribe = setUnauthorizedHandler(handler)
    tokenStorage.set('old-session')
    fakeServer(401, {}, {}, () => tokenStorage.set('new-session'))
    await expect(api.get('/progress/dashboard')).rejects.toBeTruthy()
    expect(handler).not.toHaveBeenCalled()
    unsubscribe()
  })

  it.each([400, 403, 404, 409, 429, 500, 503])('does not end the session on %i', async (status) => {
    const handler = vi.fn()
    const unsubscribe = setUnauthorizedHandler(handler)
    tokenStorage.set('valid')
    fakeServer(status)
    await expect(api.get('/topics/all')).rejects.toBeTruthy()
    expect(handler).not.toHaveBeenCalled()
    unsubscribe()
  })

  it('unsubscribing an old handler keeps a newer one', async () => {
    const first = vi.fn()
    const second = vi.fn()
    const unsubscribeFirst = setUnauthorizedHandler(first)
    const unsubscribeSecond = setUnauthorizedHandler(second)
    unsubscribeFirst()
    tokenStorage.set('expired')
    fakeServer(401)
    await expect(api.get('/auth/me')).rejects.toBeTruthy()
    expect(first).not.toHaveBeenCalled()
    expect(second).toHaveBeenCalledTimes(1)
    unsubscribeSecond()
  })
})

describe('getErrorMessage', () => {
  it("returns the backend's detail message", () => {
    expect(getErrorMessage(httpError(409, 'Email already registered'))).toBe('Email already registered')
  })

  it('explains a network failure', () => {
    expect(getErrorMessage(networkError())).toMatch(/can't reach the adaptlearn server/i)
  })

  it('explains a timeout', () => {
    expect(getErrorMessage({ isAxiosError: true, code: 'ECONNABORTED' })).toMatch(/took too long/i)
  })

  it('falls back when there is no usable detail', () => {
    expect(getErrorMessage(httpError(500))).toBe('Something went wrong. Please try again.')
    expect(getErrorMessage(httpError(500), 'Could not load topics.')).toBe('Could not load topics.')
    expect(getErrorMessage(new Error('boom'))).toBe('Something went wrong. Please try again.')
    expect(getErrorMessage(undefined)).toBe('Something went wrong. Please try again.')
  })
})

describe('getRetryAfterSeconds', () => {
  it('reads Retry-After from a 429', async () => {
    fakeServer(429, { detail: 'Too many quizzes' }, { 'retry-after': '120' })
    const error = await api.get('/quiz/generate/css_basics').catch((e) => e)
    expect(getRetryAfterSeconds(error)).toBe(120)
  })

  it('is null without the header or for other statuses', () => {
    expect(getRetryAfterSeconds({ response: { status: 429, headers: {} } })).toBeNull()
    expect(getRetryAfterSeconds({ response: { status: 503, headers: { 'retry-after': '5' } } })).toBeNull()
    expect(getRetryAfterSeconds(networkError())).toBeNull()
  })
})

describe('tokenStorage', () => {
  it('round-trips and clears the token', () => {
    tokenStorage.set('t1')
    expect(localStorage.getItem('adaptlearn.token')).toBe('t1')
    expect(tokenStorage.get()).toBe('t1')
    tokenStorage.clear()
    expect(tokenStorage.get()).toBeNull()
  })

  it('treats blocked storage as "no token" instead of crashing', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })
    expect(tokenStorage.get()).toBeNull()
    expect(() => tokenStorage.set('t')).not.toThrow()
  })
})
