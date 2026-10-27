import { afterEach, describe, expect, it, vi } from 'vitest'

import { deferred, httpError, networkError } from '@/test/helpers'

import { createEventReporter, enterFullscreen, hasMultipleScreens, leaveFullscreen } from './proctoring'

const types = (batch) => batch.map((e) => e.type)

describe('createEventReporter', () => {
  it('sends each event with the time it happened', async () => {
    const send = vi.fn().mockResolvedValue({})
    const reporter = createEventReporter(send, { now: () => Date.parse('2026-10-27T10:00:00Z') })
    reporter.record('tab_hidden')
    await reporter.flush()
    expect(send).toHaveBeenCalledWith([{ type: 'tab_hidden', occurred_at: '2026-10-27T10:00:00.000Z' }])
  })

  it('adds extra fields such as details', async () => {
    const send = vi.fn().mockResolvedValue({})
    const reporter = createEventReporter(send)
    reporter.record('multiple_screens', { details: { source: 'screen.isExtended' } })
    await reporter.flush()
    expect(send.mock.calls[0][0][0]).toMatchObject({ type: 'multiple_screens', details: { source: 'screen.isExtended' } })
  })

  it('sends one request at a time and batches events recorded meanwhile, in order', async () => {
    const first = deferred()
    const send = vi.fn().mockReturnValueOnce(first.promise).mockResolvedValue({})
    const reporter = createEventReporter(send, { now: (() => { let t = 0; return () => (t += 5000) })() })
    reporter.record('heartbeat')
    reporter.record('tab_hidden')
    reporter.record('copy_attempt')
    expect(send).toHaveBeenCalledTimes(1)
    first.resolve({})
    await reporter.flush()
    expect(send).toHaveBeenCalledTimes(2)
    expect(types(send.mock.calls[0][0])).toEqual(['heartbeat'])
    expect(types(send.mock.calls[1][0])).toEqual(['tab_hidden', 'copy_attempt'])
  })

  it('reports the same event type once within a second, but heartbeats always', async () => {
    let time = 0
    const send = vi.fn().mockResolvedValue({})
    const reporter = createEventReporter(send, { now: () => time })
    expect(reporter.record('context_menu')).toBe(true)
    time = 400
    expect(reporter.record('context_menu')).toBe(false)
    expect(reporter.record('copy_attempt')).toBe(true)
    expect(reporter.record('heartbeat')).toBe(true)
    expect(reporter.record('heartbeat')).toBe(true)
    time = 1500
    expect(reporter.record('context_menu')).toBe(true)
    await reporter.flush()
    const sent = send.mock.calls.flatMap(([batch]) => types(batch))
    expect(sent).toEqual(['context_menu', 'copy_attempt', 'heartbeat', 'heartbeat', 'context_menu'])
  })

  it('keeps events (not heartbeats) after a network failure and retries them with the next one', async () => {
    let time = 0
    const send = vi.fn().mockRejectedValueOnce(networkError()).mockResolvedValue({})
    const reporter = createEventReporter(send, { now: () => (time += 2000) })
    reporter.record('heartbeat')
    reporter.record('tab_hidden')
    await reporter.flush()
    expect(send).toHaveBeenCalledTimes(1)
    reporter.record('heartbeat')
    await reporter.flush()
    expect(types(send.mock.calls[1][0])).toEqual(['tab_hidden', 'heartbeat'])
  })

  it('drops a batch the server rejected (the quiz expired or was submitted)', async () => {
    let time = 0
    const send = vi.fn().mockRejectedValueOnce(httpError(410, 'This quiz has expired.')).mockResolvedValue({})
    const reporter = createEventReporter(send, { now: () => (time += 2000) })
    reporter.record('tab_hidden')
    await reporter.flush()
    reporter.record('heartbeat')
    await reporter.flush()
    expect(types(send.mock.calls[1][0])).toEqual(['heartbeat'])
  })

  it('splits more than 100 events into several requests', async () => {
    let time = 0
    const gate = deferred()
    const send = vi.fn().mockReturnValueOnce(gate.promise).mockResolvedValue({})
    const reporter = createEventReporter(send, { now: () => time++ })
    reporter.record('heartbeat')
    for (let i = 0; i < 150; i++) reporter.record('heartbeat')
    gate.resolve({})
    await reporter.flush()
    expect(send.mock.calls.map(([batch]) => batch.length)).toEqual([1, 100, 50])
  })

  it('sends nothing after stop', async () => {
    const send = vi.fn().mockResolvedValue({})
    const reporter = createEventReporter(send)
    reporter.stop()
    expect(reporter.record('tab_hidden')).toBe(false)
    await reporter.flush()
    expect(send).not.toHaveBeenCalled()
  })
})

describe('browser helpers', () => {
  afterEach(() => {
    delete document.documentElement.requestFullscreen
    delete document.exitFullscreen
    delete document.fullscreenElement
    delete window.screen.isExtended
  })

  it('enterFullscreen reports whether the browser allowed it', async () => {
    document.documentElement.requestFullscreen = vi.fn().mockResolvedValue()
    expect(await enterFullscreen()).toBe(true)
    document.documentElement.requestFullscreen = vi.fn().mockRejectedValue(new TypeError('not allowed'))
    expect(await enterFullscreen()).toBe(false)
  })

  it('enterFullscreen is false where fullscreen is unsupported', async () => {
    expect(await enterFullscreen()).toBe(false)
  })

  it('leaveFullscreen only exits when fullscreen is on', async () => {
    document.exitFullscreen = vi.fn().mockResolvedValue()
    await leaveFullscreen()
    expect(document.exitFullscreen).not.toHaveBeenCalled()
    Object.defineProperty(document, 'fullscreenElement', { value: document.documentElement, configurable: true })
    await leaveFullscreen()
    expect(document.exitFullscreen).toHaveBeenCalledTimes(1)
  })

  it('hasMultipleScreens reads screen.isExtended, or null where unknown', () => {
    expect(hasMultipleScreens()).toBeNull()
    Object.defineProperty(window.screen, 'isExtended', { value: true, configurable: true })
    expect(hasMultipleScreens()).toBe(true)
  })
})
