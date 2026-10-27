// Browser side of quiz proctoring (layer 2). The server scores what this page reports; see
// backend/services/proctoring.py for the rules and penalties.

/** Mirrors MIN_PLAUSIBLE_ANSWER_SECONDS: faster answers are penalised, so lock-in waits this long. */
export const MIN_ANSWER_SECONDS = 3

const MAX_BATCH = 100 // the events endpoint accepts at most 100 events per request
const MAX_QUEUE = 200
const REPEAT_WINDOW_MS = 1000

/**
 * Queue proctoring events and send them in order, one request at a time. Events that fail to send
 * because the network dropped are retried with the next event or heartbeat; heartbeats are not,
 * since the server times them on arrival. If the server rejects a batch (the quiz expired or was
 * submitted), it is dropped. The same event type within a second is reported once, so one action
 * that fires two browser events (e.g. a double right-click) costs one penalty.
 *
 * @param {(events: object[]) => Promise<unknown>} send
 */
export function createEventReporter(send, { now = () => Date.now() } = {}) {
  let queue = []
  let inFlight = null
  let stopped = false
  const lastSeen = new Map()

  async function drain() {
    while (!stopped && queue.length > 0) {
      const batch = queue.slice(0, MAX_BATCH)
      try {
        await send(batch)
        queue = queue.slice(batch.length)
      } catch (error) {
        const rest = queue.slice(batch.length)
        queue = error?.response ? rest : [...batch.filter((e) => e.type !== 'heartbeat'), ...rest]
        return
      }
    }
  }

  /** Send everything queued; resolves once the queue is empty or a send has failed. */
  function flush() {
    if (!inFlight) {
      inFlight = drain().finally(() => {
        inFlight = null
      })
    }
    return inFlight
  }

  /** Queue an event and start sending. Returns false when it was a repeat inside the window. */
  function record(type, extra = {}) {
    if (stopped) return false
    const time = now()
    if (type !== 'heartbeat') {
      const last = lastSeen.get(type)
      if (last !== undefined && time - last < REPEAT_WINDOW_MS) return false
      lastSeen.set(type, time)
    }
    queue.push({ type, occurred_at: new Date(time).toISOString(), ...extra })
    if (queue.length > MAX_QUEUE) queue = queue.slice(-MAX_QUEUE)
    // A send already running picks this event up when it finishes.
    if (!inFlight) flush()
    return true
  }

  function stop() {
    stopped = true
    queue = []
  }

  return { record, flush, stop }
}

export function isFullscreen() {
  return Boolean(document.fullscreenElement)
}

export function fullscreenSupported() {
  return typeof document.documentElement.requestFullscreen === 'function' && document.fullscreenEnabled !== false
}

/** Ask for fullscreen. Must run inside a click handler. Resolves to whether it worked. */
export async function enterFullscreen() {
  if (!fullscreenSupported()) return false
  try {
    await document.documentElement.requestFullscreen({ navigationUI: 'hide' })
    return true
  } catch {
    return false
  }
}

export async function leaveFullscreen() {
  if (!document.fullscreenElement) return
  try {
    await document.exitFullscreen()
  } catch {
    // Already left, or the browser refused; nothing to do.
  }
}

/** True or false from the Window Management API (Chromium), or null where the browser can't tell. */
export function hasMultipleScreens() {
  const extended = window.screen?.isExtended
  return typeof extended === 'boolean' ? extended : null
}
