import { useCallback, useEffect, useRef, useState } from 'react'

import { reportEvents } from '@/api/quiz'
import { createEventReporter, enterFullscreen, hasMultipleScreens, isFullscreen } from '@/lib/proctoring'

// window_blur is only sent when the tab stays visible (another app was clicked); switching tabs
// also blurs the window but is reported as tab_hidden. The check waits for visibilitychange.
const BLUR_CHECK_MS = 150

/**
 * Monitor the quiz page while `active`: heartbeats every `heartbeatSeconds`, plus tab switches,
 * window switches, leaving fullscreen, copy/cut/paste and right-click (all blocked as well as
 * reported) and a second screen. Returns what the page shows the learner about it.
 */
export function useProctoring({ quizId, active, heartbeatSeconds }) {
  const [fullscreenLost, setFullscreenLost] = useState(false)
  const [lastEvent, setLastEvent] = useState(null)
  const reporterRef = useRef(null)

  useEffect(() => {
    if (!active || !quizId) return undefined
    const reporter = createEventReporter((events) => reportEvents(quizId, events))
    reporterRef.current = reporter
    let wasFullscreen = isFullscreen()
    let blurTimer

    const note = (type, extra) => {
      if (reporter.record(type, extra)) setLastEvent({ type, at: Date.now() })
    }
    const blocked = (type) => (event) => {
      event.preventDefault()
      note(type)
    }
    const onCopy = blocked('copy_attempt')
    const onPaste = blocked('paste_attempt')
    const onContextMenu = blocked('context_menu')
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') note('tab_hidden')
    }
    const onBlur = () => {
      clearTimeout(blurTimer)
      blurTimer = setTimeout(() => {
        if (document.visibilityState === 'visible') note('window_blur')
      }, BLUR_CHECK_MS)
    }
    const onFullscreenChange = () => {
      if (isFullscreen()) {
        wasFullscreen = true
        setFullscreenLost(false)
      } else if (wasFullscreen) {
        note('fullscreen_exit')
        setFullscreenLost(true)
      }
    }
    const checkScreens = () => {
      if (hasMultipleScreens()) note('multiple_screens', { details: { source: 'screen.isExtended' } })
    }

    reporter.record('heartbeat')
    const heartbeat = setInterval(() => reporter.record('heartbeat'), heartbeatSeconds * 1000)
    checkScreens()
    document.addEventListener('copy', onCopy)
    document.addEventListener('cut', onCopy)
    document.addEventListener('paste', onPaste)
    document.addEventListener('contextmenu', onContextMenu)
    document.addEventListener('visibilitychange', onVisibility)
    document.addEventListener('fullscreenchange', onFullscreenChange)
    window.addEventListener('blur', onBlur)
    window.screen?.addEventListener?.('change', checkScreens)

    return () => {
      clearInterval(heartbeat)
      clearTimeout(blurTimer)
      document.removeEventListener('copy', onCopy)
      document.removeEventListener('cut', onCopy)
      document.removeEventListener('paste', onPaste)
      document.removeEventListener('contextmenu', onContextMenu)
      document.removeEventListener('visibilitychange', onVisibility)
      document.removeEventListener('fullscreenchange', onFullscreenChange)
      window.removeEventListener('blur', onBlur)
      window.screen?.removeEventListener?.('change', checkScreens)
      reporter.stop()
      reporterRef.current = null
      setFullscreenLost(false)
    }
  }, [quizId, active, heartbeatSeconds])

  /** Send queued events now, e.g. right before submitting so the server sees all of them. */
  const flush = useCallback(() => reporterRef.current?.flush() ?? Promise.resolve(), [])

  const returnToFullscreen = useCallback(async () => {
    if (await enterFullscreen()) setFullscreenLost(false)
  }, [])

  return { fullscreenLost, lastEvent, flush, returnToFullscreen }
}
