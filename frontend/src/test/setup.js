import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

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

const realAdapter = api.defaults.adapter

afterEach(() => {
  cleanup()
  localStorage.clear()
  api.defaults.adapter = realAdapter
})
