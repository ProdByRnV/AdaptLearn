import { useCallback, useEffect, useRef, useState } from 'react'

import { getErrorMessage, getRetryAfterSeconds } from '@/api/client'
import { answerQuestion, fetchActiveQuiz, generateQuiz, nextQuestion, submitQuiz } from '@/api/quiz'
import { fetchTopicGraph } from '@/api/topics'
import { useProctoring } from '@/hooks/useProctoring'
import { MIN_ANSWER_SECONDS, enterFullscreen, leaveFullscreen } from '@/lib/proctoring'

// The server still accepts answers for 2 s after a deadline (ANSWER_GRACE_SECONDS) and only then
// closes the question, so after a timeout the page waits before asking for the next one. If the
// expired question comes back anyway (a slow network), it asks again a little later.
const TIMEOUT_ADVANCE_MS = 2500
const TIMEOUT_RETRY_MS = 1000
const MAX_TIMEOUT_RETRIES = 5

const DEFAULT_HEARTBEAT_SECONDS = 5

/**
 * The proctored quiz flow for one topic (PRD 6.2, decision 10).
 *
 * stage: "loading" -> "intro" (no quiz yet) -> "preparing" (generating) -> "ready" (rules shown;
 * also where an unfinished quiz on this topic resumes) -> "running" (one question at a time) ->
 * "submitting" -> "result". "load-error" and "ended" (expired, already submitted, not found) are
 * the dead ends. Monitoring runs during "running" and "submitting" only.
 */
export function useQuizSession(topicId) {
  const [stage, setStage] = useState('loading')
  const [loadError, setLoadError] = useState(null)
  const [graph, setGraph] = useState(null)
  const [otherActive, setOtherActive] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [startError, setStartError] = useState(null)
  const [question, setQuestion] = useState(null)
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(null) // "next" | "answer" | "timeout" | null
  const [notice, setNotice] = useState(null)
  const [stepError, setStepError] = useState(null)
  const [fullscreenDenied, setFullscreenDenied] = useState(false)
  const [result, setResult] = useState(null)
  const [ended, setEnded] = useState(null) // "expired" | "submitted" | "missing"

  const alive = useRef(true)
  const loadId = useRef(0)
  const timer = useRef(null)

  const monitoring = stage === 'running' || stage === 'submitting'
  const proctor = useProctoring({
    quizId: quiz?.quiz_id,
    active: monitoring,
    heartbeatSeconds: quiz?.proctoring.heartbeat_interval_seconds ?? DEFAULT_HEARTBEAT_SECONDS,
  })

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
      clearTimeout(timer.current)
      leaveFullscreen()
    }
  }, [])

  useEffect(() => {
    if (!monitoring) leaveFullscreen()
  }, [monitoring])

  const load = useCallback(async () => {
    const id = ++loadId.current
    try {
      const [topicGraph, active] = await Promise.all([fetchTopicGraph(), fetchActiveQuiz()])
      if (!alive.current || id !== loadId.current) return
      setGraph(topicGraph)
      if (active?.topic.id === topicId) {
        setQuiz(active)
        setStage('ready')
      } else {
        setOtherActive(active)
        setStage('intro')
      }
    } catch (error) {
      if (!alive.current || id !== loadId.current) return
      setLoadError(error)
      setStage('load-error')
    }
  }, [topicId])

  // load only sets state after the requests answer, which the lint rule can't see through the await.
  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    load()
  }, [load])

  /** Back to the start (after a result, an expired quiz, or a load error), with fresh data. */
  function restart() {
    clearTimeout(timer.current)
    setStage('loading')
    setLoadError(null)
    setOtherActive(null)
    setQuiz(null)
    setStartError(null)
    setQuestion(null)
    setSelected(null)
    setBusy(null)
    setNotice(null)
    setStepError(null)
    setFullscreenDenied(false)
    setResult(null)
    setEnded(null)
    load()
  }

  async function prepare() {
    setStage('preparing')
    setStartError(null)
    try {
      const info = await generateQuiz(topicId)
      if (!alive.current) return
      setQuiz(info)
      setOtherActive(null)
      setStage('ready')
    } catch (error) {
      if (!alive.current) return
      const retryAfter = getRetryAfterSeconds(error)
      setStartError({
        status: error?.response?.status ?? null,
        message: getErrorMessage(error, "Couldn't create the quiz. Please try again."),
        retryAfter,
        retryAt: retryAfter === null ? null : Date.now() + retryAfter * 1000,
      })
      setStage('intro')
    }
  }

  /** Start or resume. Runs in the click handler, so the browser allows fullscreen. */
  function begin() {
    enterFullscreen().then((ok) => alive.current && setFullscreenDenied(!ok))
    setStage('running')
    setNotice(null)
    loadQuestion()
  }

  function end(reason) {
    clearTimeout(timer.current)
    setEnded(reason)
    setStage('ended')
  }

  /** 410 expired, 404 not found, 409 conflict (`onConflict`, or already submitted); else retryable. */
  function handleError(error, retry, onConflict) {
    if (!alive.current) return
    const status = error?.response?.status
    if (status === 410) return end('expired')
    if (status === 404) return end('missing')
    if (status === 409) return onConflict ? onConflict() : end('submitted')
    setBusy(null)
    setStepError({ message: getErrorMessage(error), retry })
  }

  async function loadQuestion({ expiredId = null, tries = 0 } = {}) {
    setBusy('next')
    setStepError(null)
    try {
      const served = await nextQuestion(quiz.quiz_id)
      if (!alive.current) return
      if (expiredId !== null && served.question_id === expiredId) {
        if (tries < MAX_TIMEOUT_RETRIES) {
          timer.current = setTimeout(() => loadQuestion({ expiredId, tries: tries + 1 }), TIMEOUT_RETRY_MS)
          return
        }
        setBusy(null)
        setStepError({
          message: "Time is up on this question, but the server hasn't closed it yet.",
          retry: () => loadQuestion({ expiredId }),
        })
        return
      }
      const now = Date.now()
      // A resumed question was served earlier, so part of the reading time has already passed.
      const wait = Math.max(0, MIN_ANSWER_SECONDS - (quiz.seconds_per_question - served.seconds_remaining))
      setQuestion({
        ...served,
        endsAt: now + served.seconds_remaining * 1000,
        readyAt: wait > 0 ? now + wait * 1000 : 0, // 0: ready at once
      })
      setSelected(null)
      setBusy(null)
    } catch (error) {
      // 409 here means every question is closed: the quiz only needs submitting.
      handleError(error, () => loadQuestion({ expiredId, tries }), finish)
    }
  }

  async function lockIn(questionId, answer) {
    setBusy('answer')
    setStepError(null)
    try {
      const ack = await answerQuestion(quiz.quiz_id, questionId, answer)
      if (!alive.current) return
      setNotice(
        ack.accepted
          ? null
          : `Your answer to question ${questionId + 1} arrived after its time limit, so it counts as wrong.`,
      )
      if (ack.remaining_questions > 0) loadQuestion()
      else finish()
    } catch (error) {
      handleError(error, () => lockIn(questionId, answer), () => {
        setNotice(`Question ${questionId + 1} had already closed, so that answer wasn't recorded.`)
        loadQuestion()
      })
    }
  }

  /** The countdown reached zero: submit the selected answer, or let the question time out. */
  function expire() {
    if (!question || busy) return
    if (selected !== null) {
      lockIn(question.question_id, selected)
      return
    }
    setBusy('timeout')
    setNotice(`Time ran out on question ${question.number}, so it counts as wrong.`)
    const expiredId = question.question_id
    timer.current = setTimeout(() => loadQuestion({ expiredId }), TIMEOUT_ADVANCE_MS)
  }

  async function finish() {
    setStage('submitting')
    setBusy(null)
    setStepError(null)
    try {
      await proctor.flush()
      const scored = await submitQuiz(quiz.quiz_id)
      if (!alive.current) return
      setResult(scored)
      setStage('result')
    } catch (error) {
      handleError(error, finish)
    }
  }

  return {
    stage,
    loadError,
    graph,
    otherActive,
    quiz,
    startError,
    question,
    selected,
    busy,
    notice,
    stepError,
    fullscreenDenied,
    result,
    ended,
    monitoring,
    proctor,
    select: setSelected,
    restart,
    prepare,
    begin,
    lockIn: () => question && selected !== null && lockIn(question.question_id, selected),
    expire,
  }
}
