import api from './client'

// The proctored quiz flow (backend Phase 12.5). Questions arrive one at a time and the answer key
// only comes back with the result, so no response before submission ever holds a correct answer.

// Writing the questions and checking every answer can take the server up to 20 s; allow a little more.
const GENERATE_TIMEOUT_MS = 25_000

/**
 * Create a quiz for a topic. Returns no questions; any unfinished quiz is abandoned (never counts).
 * @returns {Promise<{quiz_id: string, topic: {id: string, name: string}, total_questions: number,
 *   answered_questions: number, seconds_per_question: number, expires_in_seconds: number,
 *   source: 'ai'|'fallback'|'mixed'|null, proctoring: {verified_threshold: number, heartbeat_interval_seconds: number,
 *   rules: {code: string, penalty: number, message: string}[]}}>}
 */
export async function generateQuiz(topicId) {
  const { data } = await api.get(`/quiz/generate/${encodeURIComponent(topicId)}`, { timeout: GENERATE_TIMEOUT_MS })
  return data
}

/** The learner's unfinished quiz (same shape as generateQuiz, without `source`), or null. */
export async function fetchActiveQuiz() {
  const { data } = await api.get('/quiz/active')
  return data.active
}

/**
 * Serve the current question and start its timer. Asking again returns the same question with the
 * time that is left.
 * @returns {Promise<{question_id: number, number: number, total: number, question: string,
 *   options: string[], deadline: string, seconds_remaining: number}>}
 */
export async function nextQuestion(quizId) {
  const { data } = await api.post(`/quiz/${quizId}/next`)
  return data
}

/** Lock in an answer. @returns {Promise<{question_id: number, accepted: boolean, timed_out: boolean, remaining_questions: number}>} */
export async function answerQuestion(quizId, questionId, answer) {
  const { data } = await api.post(`/quiz/${quizId}/answer`, { question_id: questionId, answer })
  return data
}

/** Proctoring signals: heartbeats and browser events. @returns {Promise<{accepted: number, ignored: number}>} */
export async function reportEvents(quizId, events) {
  const { data } = await api.post(`/quiz/${quizId}/events`, { events })
  return data
}

/** Score the quiz and judge its integrity. A flagged attempt is recorded but changes nothing. */
export async function submitQuiz(quizId) {
  const { data } = await api.post('/quiz/submit', { quiz_id: quizId })
  return data
}
