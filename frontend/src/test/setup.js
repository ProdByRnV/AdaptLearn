import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'

import api from '@/api/client'

// Browser APIs that jsdom lacks but Radix (menus, popovers) calls.
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
Element.prototype.hasPointerCapture ??= () => false
Element.prototype.releasePointerCapture ??= () => {}
Element.prototype.scrollIntoView ??= () => {}

// Tests must never reach a real server (a dev backend may be running on this machine). Requests
// go through fakeServer() or a mocked API module; anything else fails loudly here.
export const unexpectedRequests = []
function noNetwork(config) {
  const request = `${config.method?.toUpperCase()} ${config.url}`
  unexpectedRequests.push(request)
  return Promise.reject(new Error(`Unexpected real request in a test: ${request}`))
}

beforeEach(() => {
  unexpectedRequests.length = 0
  api.defaults.adapter = noNetwork
})

afterEach(() => {
  cleanup()
  localStorage.clear()
  if (unexpectedRequests.length > 0) {
    throw new Error(`Test made real HTTP requests: ${unexpectedRequests.join(', ')}`)
  }
})
