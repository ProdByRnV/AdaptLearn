// A small slice of the real curriculum, in the API's order (difficulty, then name).
const topic = (id, name, difficulty, prerequisites, status = prerequisites.length ? 'locked' : 'unlocked') => ({
  id,
  name,
  description: `What ${name} covers.`,
  difficulty,
  status,
  mastery: 10,
  mastered: false,
  prerequisites,
  resources: [],
})

const minutesAgo = (minutes) => new Date(Date.now() - minutes * 60_000).toISOString()

/** A /progress/dashboard response for a learner a few quizzes in. Override any part. */
export function dashboard(overrides = {}) {
  const base = {
    domain: 'web-development',
    onboarded: true,
    curriculum_complete: false,
    stats: {
      total_topics: 30,
      completed_topics: 7,
      in_progress_topics: 2,
      mastered_topics: 5,
      average_mastery: 41.26,
      total_attempts: 6,
      flagged_attempts: 1,
      progress_percent: 23.3,
    },
    recommended: [
      {
        id: 'sql_basics', name: 'SQL Basics', description: 'Querying relational data with SELECT and JOIN.',
        difficulty: 2, status: 'in_progress', mastery: 45.5, prerequisites: [], prerequisite_names: [],
      },
      {
        id: 'css_grid', name: 'CSS Grid', description: 'Two-dimensional layout with rows and columns.',
        difficulty: 2, status: 'in_progress', mastery: 30, prerequisites: ['css_basics'], prerequisite_names: ['CSS Basics'],
      },
      {
        id: 'react_router', name: 'React Router', description: 'Client-side routing in React apps.',
        difficulty: 3, status: 'unlocked', mastery: 10, prerequisites: ['react_fundamentals', 'es_modules'],
        prerequisite_names: ['React Fundamentals', 'ES Modules'],
      },
    ],
    needs_attention: [
      {
        id: 'sql_basics', name: 'SQL Basics', difficulty: 2, mastery: 45.5, attempts: 3,
        resources: [
          { title: 'SQLBolt lessons', url: 'https://sqlbolt.com/', type: 'article' },
          { title: 'PostgreSQL tutorial', url: 'https://www.postgresql.org/docs/current/tutorial.html', type: 'docs' },
        ],
      },
    ],
    recent_attempts: [
      {
        id: 12, topic_id: 'git_basics', topic_name: 'Git Basics', score: 3, total: 3, passed: true,
        mastery_before: 10, mastery_after: 98.9, created_at: minutesAgo(1), counted: false,
        integrity_verdict: 'flagged', integrity_score: 75,
      },
      {
        id: 11, topic_id: 'sql_basics', topic_name: 'SQL Basics', score: 1, total: 3, passed: false,
        mastery_before: 45.7, mastery_after: 45.5, created_at: minutesAgo(5), counted: true,
        integrity_verdict: 'verified', integrity_score: 100,
      },
      {
        id: 10, topic_id: 'css_grid', topic_name: 'CSS Grid', score: 3, total: 3, passed: true,
        mastery_before: 10, mastery_after: 98.9, created_at: minutesAgo(180), counted: true,
        integrity_verdict: null, integrity_score: null,
      },
    ],
    mastery: [
      { id: 'html_basics', name: 'HTML Basics', difficulty: 1, status: 'completed', mastery: 98.9, mastered: true },
      { id: 'sql_basics', name: 'SQL Basics', difficulty: 2, status: 'in_progress', mastery: 45.5, mastered: false },
      { id: 'react_router', name: 'React Router', difficulty: 3, status: 'unlocked', mastery: 10, mastered: false },
      { id: 'testing_basics', name: 'Testing Basics', difficulty: 4, status: 'locked', mastery: 10, mastered: false },
      { id: 'deployment_basics', name: 'Deployment Basics', difficulty: 4, status: 'locked', mastery: 10, mastered: false },
    ],
  }
  return { ...base, ...overrides, stats: { ...base.stats, ...overrides.stats } }
}

export function topicGraph({ completed = [] } = {}) {
  const nodes = [
    topic('css_basics', 'CSS Basics', 1, ['html_basics']),
    topic('html_basics', 'HTML Basics', 1, []),
    topic('javascript_fundamentals', 'JavaScript Fundamentals', 1, ['html_basics']),
    topic('flexbox', 'Flexbox', 2, ['css_basics']),
    topic('props_state', 'Props & State', 2, ['react_fundamentals']),
    topic('react_fundamentals', 'React Fundamentals', 2, ['javascript_fundamentals']),
    topic('react_hooks', 'React Hooks', 3, ['props_state']),
    topic('react_router', 'React Router', 3, ['react_fundamentals']),
    topic('deployment_basics', 'Deployment Basics', 4, ['react_router']),
  ].map((t) => (completed.includes(t.id) ? { ...t, status: 'completed', mastery: 95, mastered: true } : t))
  const links = nodes.flatMap((t) => t.prerequisites.map((source) => ({ source, target: t.id })))
  return { domain: 'web-development', nodes, links }
}

const RULES = [
  { code: 'tab_hidden', penalty: 10, message: 'Switched to another tab' },
  { code: 'window_blur', penalty: 5, message: 'Switched to another window' },
  { code: 'fullscreen_exit', penalty: 15, message: 'Left fullscreen' },
  { code: 'copy_attempt', penalty: 10, message: 'Tried to copy question text' },
  { code: 'paste_attempt', penalty: 10, message: 'Tried to paste' },
  { code: 'context_menu', penalty: 5, message: 'Opened the right-click menu' },
  { code: 'multiple_screens', penalty: 20, message: 'A second screen was detected' },
  { code: 'fast_answer', penalty: 10, message: 'Answered in under 3 seconds' },
]

/** A /quiz/generate (or /quiz/active) response. */
export function quizInfo(overrides = {}) {
  return {
    quiz_id: 'quiz-1',
    topic: { id: 'html_basics', name: 'HTML Basics' },
    total_questions: 3,
    answered_questions: 0,
    seconds_per_question: 60,
    expires_in_seconds: 1800,
    source: 'ai',
    proctoring: { verified_threshold: 80, heartbeat_interval_seconds: 5, rules: RULES },
    ...overrides,
  }
}

/**
 * A /quiz/{id}/next response for question `number` (1-based). seconds_remaining defaults to 57,
 * so the minimum reading time has already passed and the answer can be locked in at once.
 */
export function quizQuestion(number = 1, overrides = {}) {
  return {
    question_id: number - 1,
    number,
    total: 3,
    question: `Question text ${number}?`,
    options: [`Option ${number}A`, `Option ${number}B`, `Option ${number}C`, `Option ${number}D`],
    deadline: new Date(Date.now() + 57_000).toISOString(),
    seconds_remaining: 57,
    ...overrides,
  }
}

/** A /quiz/submit response: 2 of 3, passed and verified. Override any part. */
export function quizResult(overrides = {}) {
  const base = {
    topic_id: 'html_basics',
    score: 2,
    total: 3,
    passed: true,
    p_know_before: 0.1,
    p_know_after: 0.762,
    mastered: false,
    status: 'completed',
    needs_attention: false,
    feedback: [
      { question: 'Which tag makes the main heading?', options: ['<header>', '<title>', '<h1>', '<h3>'], selected: 2, correct: 2, is_correct: true, timed_out: false, explanation: '<h1> is the top-level heading.' },
      { question: 'Which attribute holds the image path?', options: ['href', 'src', 'link', 'path'], selected: 1, correct: 1, is_correct: true, timed_out: false, explanation: 'src points to the image file.' },
      { question: 'Which list is unordered?', options: ['<ul>', '<ol>', '<dl>', '<list>'], selected: 1, correct: 0, is_correct: false, timed_out: false, explanation: '<ul> is an unordered list.' },
    ],
    recommended_resources: [],
    newly_unlocked: ['css_basics', 'javascript_fundamentals'],
    next_topics: [
      { id: 'css_basics', name: 'CSS Basics', description: 'Styling pages.', difficulty: 1, status: 'unlocked', mastery: 10, prerequisites: ['html_basics'], prerequisite_names: ['HTML Basics'] },
    ],
    integrity: { score: 100, verdict: 'verified', counted: true, reasons: [] },
  }
  return { ...base, ...overrides, integrity: { ...base.integrity, ...overrides.integrity } }
}
