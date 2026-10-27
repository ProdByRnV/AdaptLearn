import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { fetchDashboard } from '@/api/progress'
import { answerQuestion, fetchActiveQuiz, generateQuiz, nextQuestion, reportEvents, submitQuiz } from '@/api/quiz'
import { fetchTopicGraph } from '@/api/topics'
import { quizInfo, quizQuestion, quizResult, topicGraph } from '@/test/fixtures'
import { httpError, LEARNER, networkError } from '@/test/helpers'
import { renderAt } from '@/test/render-app'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/api/topics', () => ({ fetchLearningPath: vi.fn(), fetchTopicGraph: vi.fn(), markKnownTopics: vi.fn() }))
vi.mock('@/api/progress', () => ({ fetchDashboard: vi.fn() }))
vi.mock('@/api/quiz', () => ({
  generateQuiz: vi.fn(),
  fetchActiveQuiz: vi.fn(),
  nextQuestion: vi.fn(),
  answerQuestion: vi.fn(),
  reportEvents: vi.fn(),
  submitQuiz: vi.fn(),
}))

// jsdom has no Fullscreen API: a fake that behaves like the browser's.
let fullscreen = false
function setFullscreen(on) {
  fullscreen = on
  document.dispatchEvent(new Event('fullscreenchange'))
}

beforeEach(() => {
  Object.defineProperty(document, 'fullscreenElement', {
    configurable: true,
    get: () => (fullscreen ? document.documentElement : null),
  })
  document.documentElement.requestFullscreen = vi.fn(async () => setFullscreen(true))
  document.exitFullscreen = vi.fn(async () => setFullscreen(false))
  tokenStorage.set('jwt')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  fetchTopicGraph.mockResolvedValue(topicGraph())
  fetchActiveQuiz.mockResolvedValue(null)
  fetchDashboard.mockReturnValue(new Promise(() => {}))
  generateQuiz.mockResolvedValue(quizInfo())
  reportEvents.mockResolvedValue({ accepted: 1, ignored: 0 })
  nextQuestion
    .mockResolvedValueOnce(quizQuestion(1))
    .mockResolvedValueOnce(quizQuestion(2))
    .mockResolvedValueOnce(quizQuestion(3))
  answerQuestion.mockImplementation(async (_quizId, questionId) => ({
    question_id: questionId,
    accepted: true,
    timed_out: false,
    remaining_questions: 2 - questionId,
  }))
  submitQuiz.mockResolvedValue(quizResult())
})

afterEach(() => {
  vi.useRealTimers()
  fullscreen = false
  delete document.fullscreenElement
  delete document.visibilityState
  delete document.documentElement.requestFullscreen
  delete document.exitFullscreen
  delete window.screen.isExtended
})

async function open(topic = 'html_basics', { timers = false } = {}) {
  if (timers) vi.useFakeTimers({ shouldAdvanceTime: true })
  const user = userEvent.setup(timers ? { advanceTimers: vi.advanceTimersByTime } : {})
  const view = renderAt(`/quiz/${topic}`)
  await screen.findByRole('heading', { level: 1 })
  await waitFor(() => expect(screen.queryByText('Loading quiz…')).not.toBeInTheDocument())
  return { user, ...view }
}

async function startQuiz(user) {
  await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
  await user.click(await screen.findByRole('button', { name: 'Enter fullscreen and start' }))
  await screen.findByRole('heading', { name: 'Question text 1?' })
}

async function answer(user, option) {
  await user.click(screen.getByRole('radio', { name: option }))
  await user.click(screen.getByRole('button', { name: /^Lock in/ }))
}

async function takeWholeQuiz(user) {
  await startQuiz(user)
  await answer(user, 'Option 1C')
  await screen.findByRole('heading', { name: 'Question text 2?' })
  await answer(user, 'Option 2B')
  await screen.findByRole('heading', { name: 'Question text 3?' })
  await answer(user, 'Option 3B')
  await screen.findByRole('heading', { name: 'You passed' })
}

const sentEvents = () => reportEvents.mock.calls.flatMap(([, events]) => events.map((e) => e.type))
const advance = (ms) => act(() => vi.advanceTimersByTimeAsync(ms))
const fire = (target, type) => act(() => target.dispatchEvent(new Event(type, { bubbles: true, cancelable: true })))
function setVisibility(state) {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true })
  return fire(document, 'visibilitychange')
}

describe('before the quiz', () => {
  it('introduces the topic and only creates a quiz when asked', async () => {
    await open()
    expect(screen.getByRole('heading', { level: 1, name: 'HTML Basics quiz' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'How the quiz works' })).toBeInTheDocument()
    expect(screen.getByText('Answer 2 of 3 correctly to pass and raise your mastery.')).toBeInTheDocument()
    expect(screen.getByText('Unlocked')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Prepare quiz' })).toBeEnabled()
    expect(fetchActiveQuiz).toHaveBeenCalledTimes(1)
    expect(generateQuiz).not.toHaveBeenCalled()
  })

  it('explains a locked topic instead of offering the quiz', async () => {
    await open('css_basics')
    expect(screen.getByText('This topic is locked')).toBeInTheDocument()
    expect(screen.getByText(/Complete HTML Basics first\./)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Prepare quiz' })).not.toBeInTheDocument()
  })

  it('says when the topic does not exist', async () => {
    await open('quantum_basics')
    expect(screen.getByRole('heading', { name: 'Topic not found' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to dashboard' })).toHaveAttribute('href', '/dashboard')
  })

  it('offers a retry when the page cannot load', async () => {
    fetchActiveQuiz.mockRejectedValueOnce(networkError())
    const { user } = await open()
    expect(screen.getByRole('heading', { name: "Couldn't load the quiz" })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('button', { name: 'Prepare quiz' })).toBeInTheDocument()
  })

  it('warns that starting abandons an unfinished quiz on another topic', async () => {
    fetchActiveQuiz.mockResolvedValue(
      quizInfo({ topic: { id: 'javascript_fundamentals', name: 'JavaScript Fundamentals' }, answered_questions: 1, source: null }),
    )
    await open()
    expect(screen.getByText('You have an unfinished quiz on JavaScript Fundamentals')).toBeInTheDocument()
    expect(screen.getByText(/1 of 3 questions answered\. Starting this quiz abandons it/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Resume JavaScript Fundamentals instead' })).toHaveAttribute(
      'href',
      '/quiz/javascript_fundamentals',
    )
  })

  it('resumes an unfinished quiz on this topic without creating a new one', async () => {
    fetchActiveQuiz.mockResolvedValue(quizInfo({ answered_questions: 1, source: null }))
    nextQuestion.mockReset().mockResolvedValueOnce(quizQuestion(2, { seconds_remaining: 20 }))
    const { user } = await open()
    expect(screen.getByRole('heading', { name: 'Resume your quiz' })).toBeInTheDocument()
    expect(screen.getByText(/You've answered 1 of 3 questions/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Enter fullscreen and resume' }))
    expect(await screen.findByRole('heading', { name: 'Question text 2?' })).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent('0:20')
    expect(generateQuiz).not.toHaveBeenCalled()
  })
})

describe('preparing', () => {
  it("shows the server's rules before the first question", async () => {
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    expect(await screen.findByRole('heading', { name: 'Your quiz is ready' })).toBeInTheDocument()
    expect(generateQuiz).toHaveBeenCalledWith('html_basics')
    expect(screen.getByText('60s')).toBeInTheDocument()
    expect(screen.getByText('30 min')).toBeInTheDocument()
    expect(screen.getByText(/The attempt counts if it stays at 80 or more/)).toBeInTheDocument()
    const rules = within(screen.getByRole('region', { name: 'Integrity rules' })).getAllByRole('listitem')
    expect(rules).toHaveLength(8)
    expect(rules[0]).toHaveTextContent('Switched to another tab−10 points')
    expect(screen.queryByText('Questions from the curated bank')).not.toBeInTheDocument()
    expect(nextQuestion).not.toHaveBeenCalled()
  })

  it('says when the questions come from the fallback bank', async () => {
    generateQuiz.mockResolvedValue(quizInfo({ source: 'fallback' }))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    expect(await screen.findByText('Questions from the curated bank')).toBeInTheDocument()
  })

  it('shows the wait from Retry-After when the quiz limit is reached', async () => {
    const limited = httpError(429, 'Too many quizzes started for this topic in the last hour. Try again in about 12 minute(s).')
    limited.response.headers = { 'retry-after': '720' }
    generateQuiz.mockRejectedValueOnce(limited)
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    expect(await screen.findByText('Quiz limit reached')).toBeInTheDocument()
    expect(screen.getByText(/Try again in about 12 minute/)).toBeInTheDocument()
    expect(screen.getByText(/You can start another quiz in/)).toHaveTextContent('12:00')
    expect(screen.getByRole('button', { name: 'Prepare quiz' })).toBeDisabled()
  })

  it.each([
    [403, 'Topic is still locked. Complete its prerequisites first.', 'This topic is locked'],
    [503, 'Quiz generation is temporarily unavailable. Please try again shortly.', 'Quiz generation is unavailable'],
  ])('explains a %s and lets the learner try again', async (status, detail, title) => {
    generateQuiz.mockRejectedValueOnce(httpError(status, detail))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    expect(await screen.findByText(title)).toBeInTheDocument()
    expect(screen.getByText(detail)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    expect(await screen.findByRole('heading', { name: 'Your quiz is ready' })).toBeInTheDocument()
  })
})

describe('taking the quiz', () => {
  it('enters fullscreen, hides the navigation and shows one question with the server time', async () => {
    nextQuestion.mockReset().mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 42 }))
    const { user } = await open()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    await startQuiz(user)
    expect(document.documentElement.requestFullscreen).toHaveBeenCalled()
    expect(screen.queryByRole('navigation', { name: 'Main' })).not.toBeInTheDocument()
    expect(screen.getByRole('timer', { name: 'Time left: 42 seconds' })).toHaveTextContent('0:42')
    expect(screen.getAllByRole('radio')).toHaveLength(4)
    expect(screen.getByRole('heading', { name: 'Question text 1?' })).toHaveFocus()
    expect(screen.queryByText('Question text 2?')).not.toBeInTheDocument()
  })

  it('locks in each answer, then submits and shows the result', async () => {
    const { user } = await open()
    await startQuiz(user)
    const lock = screen.getByRole('button', { name: 'Lock in answer' })
    expect(lock).toBeDisabled()
    await answer(user, 'Option 1C')
    expect(answerQuestion).toHaveBeenLastCalledWith('quiz-1', 0, 2)
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2B')
    expect(answerQuestion).toHaveBeenLastCalledWith('quiz-1', 1, 1)
    await screen.findByRole('heading', { name: 'Question text 3?' })
    expect(screen.getByRole('button', { name: 'Lock in and finish' })).toBeInTheDocument()
    await answer(user, 'Option 3A')
    expect(answerQuestion).toHaveBeenLastCalledWith('quiz-1', 2, 0)
    expect(await screen.findByRole('heading', { name: 'You passed' })).toBeInTheDocument()
    expect(submitQuiz).toHaveBeenCalledWith('quiz-1')
    expect(nextQuestion).toHaveBeenCalledTimes(3)
    expect(document.exitFullscreen).toHaveBeenCalled()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
  })

  it('ignores a double click on lock in', async () => {
    const { user } = await open()
    await startQuiz(user)
    await user.click(screen.getByRole('radio', { name: 'Option 1A' }))
    const lock = screen.getByRole('button', { name: 'Lock in answer' })
    fireEvent.submit(lock.closest('form'))
    fireEvent.submit(lock.closest('form'))
    await screen.findByRole('heading', { name: 'Question text 2?' })
    expect(answerQuestion).toHaveBeenCalledTimes(1)
  })

  it('waits a moment before an answer can be locked in', async () => {
    nextQuestion.mockReset().mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 60 }))
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    await user.click(screen.getByRole('radio', { name: 'Option 1A' }))
    expect(screen.getByRole('button', { name: 'Lock in answer' })).toBeDisabled()
    expect(screen.getByText('Take a moment to read the question.')).toBeInTheDocument()
    await advance(3100)
    expect(screen.getByRole('button', { name: 'Lock in answer' })).toBeEnabled()
    expect(screen.getByText("Answers can't be changed once locked in.")).toBeInTheDocument()
  })

  it('lets an unanswered question time out, then moves on', async () => {
    nextQuestion
      .mockReset()
      .mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 1 }))
      .mockResolvedValueOnce(quizQuestion(2))
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    await advance(1300)
    expect(screen.getByText("Time's up")).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Option 1A' })).toBeDisabled()
    expect(nextQuestion).toHaveBeenCalledTimes(1)
    await advance(2600)
    expect(await screen.findByRole('heading', { name: 'Question text 2?' })).toBeInTheDocument()
    expect(screen.getByText('Time ran out on question 1, so it counts as wrong.')).toBeInTheDocument()
    expect(answerQuestion).not.toHaveBeenCalled()
  })

  it('asks again if the expired question comes back', async () => {
    nextQuestion
      .mockReset()
      .mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 1 }))
      .mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 0 }))
      .mockResolvedValueOnce(quizQuestion(2))
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    await advance(1300)
    await advance(2600)
    expect(nextQuestion).toHaveBeenCalledTimes(2)
    await advance(1100)
    expect(await screen.findByRole('heading', { name: 'Question text 2?' })).toBeInTheDocument()
  })

  it('submits the selected answer when time runs out', async () => {
    nextQuestion
      .mockReset()
      .mockResolvedValueOnce(quizQuestion(1, { seconds_remaining: 1 }))
      .mockResolvedValueOnce(quizQuestion(2))
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    await user.click(screen.getByRole('radio', { name: 'Option 1D' }))
    await advance(1300)
    expect(answerQuestion).toHaveBeenCalledWith('quiz-1', 0, 3)
    expect(await screen.findByRole('heading', { name: 'Question text 2?' })).toBeInTheDocument()
  })

  it('says when an answer arrived too late', async () => {
    answerQuestion.mockResolvedValueOnce({ question_id: 0, accepted: false, timed_out: true, remaining_questions: 2 })
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1A')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    expect(screen.getByText(/Your answer to question 1 arrived after its time limit/)).toBeInTheDocument()
  })

  it('offers a retry when an answer cannot be sent', async () => {
    answerQuestion.mockRejectedValueOnce(networkError())
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1B')
    expect(await screen.findByRole('heading', { name: "Couldn't reach the server" })).toBeInTheDocument()
    expect(screen.getByText(/The timer keeps running on the server\./)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'Question text 2?' })).toBeInTheDocument()
    expect(answerQuestion).toHaveBeenCalledTimes(2)
    expect(answerQuestion).toHaveBeenLastCalledWith('quiz-1', 0, 1)
  })

  it('moves on when the question had already closed', async () => {
    answerQuestion.mockRejectedValueOnce(httpError(409, 'That question is not open.'))
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1B')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    expect(screen.getByText(/Question 1 had already closed/)).toBeInTheDocument()
  })

  it('submits straight away when a resumed quiz has no questions left', async () => {
    fetchActiveQuiz.mockResolvedValue(quizInfo({ answered_questions: 3, source: null }))
    nextQuestion.mockReset().mockRejectedValueOnce(httpError(409, 'All questions have been answered. Submit the quiz.'))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Enter fullscreen and resume' }))
    expect(await screen.findByRole('heading', { name: 'You passed' })).toBeInTheDocument()
    expect(submitQuiz).toHaveBeenCalledWith('quiz-1')
  })

  it('offers a retry when submitting fails, without losing anything', async () => {
    submitQuiz.mockRejectedValueOnce(httpError(503, 'A database is temporarily unavailable. Nothing was saved.'))
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1A')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2A')
    await screen.findByRole('heading', { name: 'Question text 3?' })
    await answer(user, 'Option 3A')
    expect(await screen.findByRole('heading', { name: "Couldn't submit your quiz" })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'You passed' })).toBeInTheDocument()
    expect(submitQuiz).toHaveBeenCalledTimes(2)
  })

  it.each([
    [410, 'This quiz has expired. Start a new quiz for this topic.', 'This quiz has expired'],
    [404, 'Quiz not found', "We couldn't find this quiz"],
  ])('ends the quiz on a %s and can start a new one', async (status, detail, title) => {
    nextQuestion.mockReset().mockRejectedValueOnce(httpError(status, detail))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    await user.click(await screen.findByRole('button', { name: 'Enter fullscreen and start' }))
    expect(await screen.findByRole('heading', { name: title })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Start a new quiz' }))
    expect(await screen.findByRole('button', { name: 'Prepare quiz' })).toBeInTheDocument()
    expect(fetchActiveQuiz).toHaveBeenCalledTimes(2)
  })

  it('says when the quiz was already submitted elsewhere', async () => {
    submitQuiz.mockRejectedValueOnce(httpError(409, 'This quiz has already been submitted'))
    fetchActiveQuiz.mockResolvedValue(quizInfo({ answered_questions: 3, source: null }))
    nextQuestion.mockReset().mockRejectedValueOnce(httpError(409, 'All questions have been answered. Submit the quiz.'))
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Enter fullscreen and resume' }))
    expect(await screen.findByRole('heading', { name: 'This quiz was already submitted' })).toBeInTheDocument()
  })
})

describe('monitoring', () => {
  it('sends a heartbeat at once and then every 5 seconds', async () => {
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    expect(sentEvents()).toContain('heartbeat')
    const before = sentEvents().filter((t) => t === 'heartbeat').length
    await advance(10_000)
    expect(sentEvents().filter((t) => t === 'heartbeat').length).toBe(before + 2)
    expect(reportEvents.mock.calls.every(([quizId]) => quizId === 'quiz-1')).toBe(true)
  })

  it('reports switching tabs and tells the learner', async () => {
    const { user } = await open()
    await startQuiz(user)
    await setVisibility('hidden')
    await waitFor(() => expect(sentEvents()).toContain('tab_hidden'))
    expect(screen.getByText('Recorded: Switched to another tab (−10 integrity).')).toBeInTheDocument()
  })

  it.each([
    ['copy', 'copy_attempt'],
    ['cut', 'copy_attempt'],
    ['paste', 'paste_attempt'],
    ['contextmenu', 'context_menu'],
  ])('blocks and reports %s', async (type, event) => {
    const { user } = await open()
    await startQuiz(user)
    const dispatched = new Event(type, { bubbles: true, cancelable: true })
    act(() => {
      screen.getByRole('heading', { name: 'Question text 1?' }).dispatchEvent(dispatched)
    })
    expect(dispatched.defaultPrevented).toBe(true)
    await waitFor(() => expect(sentEvents()).toContain(event))
  })

  it('reports switching windows only while the tab stays visible', async () => {
    const { user } = await open('html_basics', { timers: true })
    await startQuiz(user)
    await fire(window, 'blur')
    await advance(200)
    expect(sentEvents()).toContain('window_blur')
    reportEvents.mockClear()
    await advance(1000)
    await fire(window, 'blur')
    await setVisibility('hidden')
    await advance(200)
    expect(sentEvents()).toContain('tab_hidden')
    expect(sentEvents()).not.toContain('window_blur')
  })

  it('reports leaving fullscreen and offers to return', async () => {
    const { user } = await open()
    await startQuiz(user)
    await act(async () => setFullscreen(false))
    await waitFor(() => expect(sentEvents()).toContain('fullscreen_exit'))
    expect(screen.getByText('You left fullscreen')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Return to fullscreen' }))
    expect(document.documentElement.requestFullscreen).toHaveBeenCalledTimes(2)
    expect(screen.queryByText('You left fullscreen')).not.toBeInTheDocument()
  })

  it('reports a second screen', async () => {
    Object.defineProperty(window.screen, 'isExtended', { value: true, configurable: true })
    const { user } = await open()
    await startQuiz(user)
    await waitFor(() => expect(sentEvents()).toContain('multiple_screens'))
  })

  it('carries on in the window when fullscreen is refused', async () => {
    document.documentElement.requestFullscreen = vi.fn().mockRejectedValue(new TypeError('Permissions check failed'))
    const { user } = await open()
    await startQuiz(user)
    expect(await screen.findByText("Fullscreen isn't available")).toBeInTheDocument()
    await act(async () => document.dispatchEvent(new Event('fullscreenchange')))
    expect(sentEvents()).not.toContain('fullscreen_exit')
  })

  it('stops after the result and does not count its own fullscreen exit', async () => {
    const { user } = await open()
    await takeWholeQuiz(user)
    expect(fullscreen).toBe(false)
    expect(sentEvents()).not.toContain('fullscreen_exit')
    reportEvents.mockClear()
    await setVisibility('hidden')
    const dispatched = new Event('copy', { bubbles: true, cancelable: true })
    act(() => {
      document.body.dispatchEvent(dispatched)
    })
    expect(dispatched.defaultPrevented).toBe(false)
    expect(reportEvents).not.toHaveBeenCalled()
  })
})

describe('leaving mid-quiz', () => {
  it('asks before navigating away, and stays on request', async () => {
    const { user, router } = await open()
    await startQuiz(user)
    act(() => {
      router.navigate('/dashboard')
    })
    const dialog = await screen.findByRole('alertdialog', { name: 'Leave the quiz?' })
    await user.click(within(dialog).getByRole('button', { name: 'Stay in the quiz' }))
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())
    expect(router.state.location.pathname).toBe('/quiz/html_basics')
    expect(screen.getByRole('heading', { name: 'Question text 1?' })).toBeInTheDocument()

    act(() => {
      router.navigate('/dashboard')
    })
    await user.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Leave' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))
    expect(document.exitFullscreen).toHaveBeenCalled()
  })

  it('warns before a reload only while the quiz runs', async () => {
    const { user } = await open()
    const unload = () => {
      const event = new Event('beforeunload', { cancelable: true })
      window.dispatchEvent(event)
      return event.defaultPrevented
    }
    expect(unload()).toBe(false)
    await startQuiz(user)
    expect(unload()).toBe(true)
  })
})

describe('the result', () => {
  it('shows score, mastery, integrity, unlocked topics and every answer', async () => {
    const { user } = await open()
    await takeWholeQuiz(user)
    expect(screen.getByRole('heading', { name: 'You passed' })).toHaveFocus()
    expect(screen.getByText(/right on/)).toHaveTextContent('You got 2 of 3 right on HTML Basics.')
    expect(screen.getByText('10% before this quiz, 76% now.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Integrity verified/ })).toHaveTextContent('100/100')
    expect(screen.getByText('Nothing was recorded during the quiz. The attempt counts.')).toBeInTheDocument()
    const unlocked = screen.getByRole('region', { name: 'New topics unlocked' })
    expect(within(unlocked).getByRole('link', { name: 'CSS Basics' })).toHaveAttribute('href', '/quiz/css_basics')
    expect(within(unlocked).getByRole('link', { name: 'JavaScript Fundamentals' })).toBeInTheDocument()

    const first = screen.getByText('Which tag makes the main heading?').closest('[data-slot="card"]')
    expect(first).toHaveTextContent('Correct')
    expect(first).toHaveTextContent('Your answer, correct')
    expect(first).toHaveTextContent('Why: <h1> is the top-level heading.')
    const third = screen.getByText('Which list is unordered?').closest('[data-slot="card"]')
    expect(third).toHaveTextContent('Wrong')
    expect(within(third).getByText('<ol>').parentElement).toHaveTextContent('Your answer')
    expect(within(third).getByText('<ul>').parentElement).toHaveTextContent('Correct answer')

    expect(screen.queryByRole('region', { name: 'Review before trying again' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Start topic: CSS Basics' })).toHaveAttribute('href', '/quiz/css_basics')
    expect(screen.getByRole('link', { name: 'Back to dashboard' })).toHaveAttribute('href', '/dashboard')
  })

  it('shows resources and a retry after a failed quiz', async () => {
    submitQuiz.mockResolvedValue(
      quizResult({
        score: 0,
        passed: false,
        p_know_after: 0.05,
        status: 'in_progress',
        newly_unlocked: [],
        recommended_resources: [{ title: 'MDN: HTML basics', url: 'https://developer.mozilla.org/', type: 'docs' }],
        feedback: quizResult().feedback.map((f) => ({ ...f, selected: null, is_correct: false, timed_out: true })),
      }),
    )
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1A')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2A')
    await screen.findByRole('heading', { name: 'Question text 3?' })
    await answer(user, 'Option 3A')
    expect(await screen.findByRole('heading', { name: 'Not quite yet' })).toBeInTheDocument()
    expect(screen.getByText(/You need 2 correct to pass\./)).toBeInTheDocument()
    expect(screen.getAllByText('Not answered in time')).toHaveLength(3)
    const resources = screen.getByRole('region', { name: 'Review before trying again' })
    const link = within(resources).getByRole('link', { name: 'MDN: HTML basics (Docs, opens in a new tab)' })
    expect(link).toHaveAttribute('target', '_blank')
    expect(screen.queryByRole('region', { name: 'New topics unlocked' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('button', { name: 'Prepare quiz' })).toBeInTheDocument()
  })

  it("explains a flagged attempt that didn't count", async () => {
    submitQuiz.mockResolvedValue(
      quizResult({
        score: 3,
        p_know_after: 0.1,
        mastered: false,
        newly_unlocked: [],
        integrity: {
          score: 65,
          verdict: 'flagged',
          counted: false,
          reasons: [
            { code: 'fullscreen_exit', count: 1, penalty: 15, message: 'Left fullscreen' },
            { code: 'tab_hidden', count: 2, penalty: 20, message: 'Switched to another tab' },
          ],
        },
      }),
    )
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1A')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2A')
    await screen.findByRole('heading', { name: 'Question text 3?' })
    await answer(user, 'Option 3A')
    expect(await screen.findByRole('heading', { name: "This attempt didn't count" })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Flagged by proctoring/ })).toHaveTextContent('65/100')
    expect(screen.getByText(/need an integrity score of 80 or more to count/)).toBeInTheDocument()
    expect(screen.getByText('Unchanged at 10%, because this attempt didn\'t count.')).toBeInTheDocument()
    expect(screen.getByText('Switched to another tab (×2)').parentElement).toHaveTextContent('−20 points')
    expect(screen.queryByText('Mastered')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('celebrates mastery', async () => {
    submitQuiz.mockResolvedValue(quizResult({ score: 3, p_know_after: 0.989, mastered: true }))
    const { user } = await open()
    await takeWholeQuiz(user)
    expect(screen.getByText('Mastered')).toBeInTheDocument()
  })

  it('starts afresh from a link back to the same topic', async () => {
    submitQuiz.mockResolvedValue(
      quizResult({
        score: 1,
        passed: false,
        newly_unlocked: [],
        next_topics: [
          { id: 'html_basics', name: 'HTML Basics', description: 'Pages.', difficulty: 1, status: 'in_progress', mastery: 30, prerequisites: [], prerequisite_names: [] },
        ],
      }),
    )
    const { user } = await open()
    await startQuiz(user)
    await answer(user, 'Option 1A')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2A')
    await screen.findByRole('heading', { name: 'Question text 3?' })
    await answer(user, 'Option 3A')
    await user.click(await screen.findByRole('link', { name: 'Retry quiz: HTML Basics' }))
    expect(await screen.findByRole('button', { name: 'Prepare quiz' })).toBeInTheDocument()
  })
})

describe('code in questions', () => {
  it('shows snippets as code in the question, options and review', async () => {
    const snippet = 'What is logged?\n```javascript\nlet count = 0;\nconsole.log(count)\n```'
    nextQuestion
      .mockReset()
      .mockResolvedValueOnce(quizQuestion(1, { question: snippet, options: ['`0`', '`1`', '`undefined`', 'An error'] }))
      .mockResolvedValueOnce(quizQuestion(2))
      .mockResolvedValueOnce(quizQuestion(3))
    submitQuiz.mockResolvedValue(
      quizResult({ feedback: quizResult().feedback.map((f, i) => (i === 0 ? { ...f, question: snippet, explanation: 'It logs `0`.' } : f)) }),
    )
    const { user } = await open()
    await user.click(screen.getByRole('button', { name: 'Prepare quiz' }))
    await user.click(await screen.findByRole('button', { name: 'Enter fullscreen and start' }))
    const heading = await screen.findByRole('heading', { name: /What is logged\?/ })
    const block = within(heading).getByText(/let count = 0;/, { selector: 'code' })
    expect(block.textContent).toBe('let count = 0;\nconsole.log(count)')
    expect(heading).not.toHaveTextContent('```')
    expect(screen.getByRole('radio', { name: 'undefined' })).toBeInTheDocument()
    expect(screen.getByText('undefined', { selector: 'code' })).toBeInTheDocument()

    await answer(user, '0')
    await screen.findByRole('heading', { name: 'Question text 2?' })
    await answer(user, 'Option 2B')
    await screen.findByRole('heading', { name: 'Question text 3?' })
    await answer(user, 'Option 3B')
    await screen.findByRole('heading', { name: 'You passed' })
    expect(screen.getByText(/let count = 0;/, { selector: 'code' })).toBeInTheDocument()
    expect(screen.getByText('0', { selector: 'p code' })).toBeInTheDocument()
  })
})
