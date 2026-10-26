import { AxiosError } from 'axios'
import { vi } from 'vitest'

import api from '@/api/client'

/**
 * Replace the HTTP layer of the real axios instance (interceptors still run) with a fake that
 * answers every request with `status`. `onRequest(config)` runs first, e.g. to change state mid-flight.
 */
export function fakeServer(status, data = {}, headers = {}, onRequest = () => {}) {
  const adapter = vi.fn(async (config) => {
    onRequest(config)
    const response = { status, statusText: String(status), data, headers, config, request: {} }
    if (status >= 200 && status < 300) return response
    throw new AxiosError(`Request failed with status code ${status}`, AxiosError.ERR_BAD_RESPONSE, config, {}, response)
  })
  api.defaults.adapter = adapter
  return adapter
}

/** An axios-shaped error, as the API helpers would reject with. */
export function httpError(status, detail) {
  const response = { status, statusText: String(status), data: detail ? { detail } : {}, headers: {}, config: {} }
  return new AxiosError(`Request failed with status code ${status}`, AxiosError.ERR_BAD_RESPONSE, {}, {}, response)
}

export function networkError() {
  return new AxiosError('Network Error', AxiosError.ERR_NETWORK, {}, {})
}

/** A promise you resolve or reject from the outside. */
export function deferred() {
  let resolve
  let reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

export const LEARNER = { id: 7, username: 'Puja Sharma', email: 'puja@example.com' }
