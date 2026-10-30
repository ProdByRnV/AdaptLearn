// A small slice of the real curriculum, in the API's order (difficulty, then name).
const topic = (id, name, difficulty, prerequisites, status = prerequisites.length ? 'locked' : 'unlocked', domain = 'web-development') => ({
  id,
  name,
  description: `What ${name} covers.`,
  difficulty,
  status,
  mastery: 10,
  mastered: false,
  prerequisites,
  external_prerequisites: [],
  domains: [domain],
  home_domain: domain,
  resources: [],
})

export const DOMAINS = [
  { id: 'foundations', name: 'Foundations' },
  { id: 'web-development', name: 'Web Development' },
]

const minutesAgo = (minutes) => new Date(Date.now() - minutes * 60_000).toISOString()

/** A /progress/dashboard response for a learner a few quizzes in. Override any part. */
export function dashboard(overrides = {}) {
  const base = {
    domain: 'web-development',
    domain_name: 'Web Development',
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

const markCompleted = (completed) => (t) =>
  completed.includes(t.id) ? { ...t, status: 'completed', mastery: 95, mastered: true } : t

function webDevelopmentTopics() {
  return [
    topic('css_basics', 'CSS Basics', 1, ['html_basics']),
    topic('html_basics', 'HTML Basics', 1, []),
    topic('javascript_fundamentals', 'JavaScript Fundamentals', 1, ['html_basics']),
    topic('flexbox', 'Flexbox', 2, ['css_basics']),
    topic('props_state', 'Props & State', 2, ['react_fundamentals']),
    topic('react_fundamentals', 'React Fundamentals', 2, ['javascript_fundamentals']),
    topic('react_hooks', 'React Hooks', 3, ['props_state']),
    topic('react_router', 'React Router', 3, ['react_fundamentals']),
    topic('deployment_basics', 'Deployment Basics', 4, ['react_router']),
  ]
}

/**
 * A /topics/graph response for Web Development. Deployment Basics also needs Command Line, from
 * Foundations, which isn't a node here: it is listed in external_prerequisites.
 */
export function topicGraph({ completed = [] } = {}) {
  const nodes = webDevelopmentTopics().map(markCompleted(completed))
  const deployment = nodes.find((t) => t.id === 'deployment_basics')
  deployment.external_prerequisites = [
    { id: 'command_line', name: 'Command Line', domain: 'foundations', domain_name: 'Foundations', completed: completed.includes('command_line') },
  ]
  const links = nodes.flatMap((t) => t.prerequisites.map((source) => ({ source, target: t.id })))
  return { domain: 'web-development', domain_name: 'Web Development', domains: DOMAINS, nodes, links }
}

/**
 * A /topics/map response: Foundations (Command Line, then Git Basics, which Web Development shares)
 * and the Web Development topics above, where Deployment Basics needs Command Line.
 */
export function topicMap({ completed = [] } = {}) {
  const foundations = [
    topic('command_line', 'Command Line', 1, [], undefined, 'foundations'),
    { ...topic('git_basics', 'Git Basics', 1, ['command_line'], undefined, 'foundations'), domains: ['foundations', 'web-development'] },
  ]
  const web = webDevelopmentTopics().map((t) =>
    t.id === 'deployment_basics' ? { ...t, prerequisites: ['react_router', 'command_line'] } : t,
  )
  const nodes = [...foundations, ...web]
    .map(markCompleted(completed))
    .sort((a, b) => a.difficulty - b.difficulty || a.name.localeCompare(b.name))
  const links = nodes.flatMap((t) => t.prerequisites.map((source) => ({ source, target: t.id })))
  return { domains: DOMAINS, nodes, links }
}

/** A domain in the /domains catalogue. Override any part. */
export function domainSummary(overrides = {}) {
  return {
    id: 'web-development',
    name: 'Web Development',
    description: 'Build websites and web apps, from HTML to deployment.',
    total_topics: 30,
    completed_topics: 0,
    in_progress_topics: 0,
    available_topics: 4,
    progress_percent: 0,
    curriculum_complete: false,
    joined: false,
    joined_at: null,
    onboarded: false,
    known_topics: [],
    ready_topics: [],
    suggested: false,
    ...overrides,
  }
}

/** A /domains response: Foundations (joined and set up) and Web Development (a head start through Git Basics). */
export function catalogue() {
  return {
    domains: [
      domainSummary({
        id: 'foundations', name: 'Foundations', description: 'The tools every programmer uses.',
        total_topics: 3, completed_topics: 1, available_topics: 2, progress_percent: 33.3,
        joined: true, joined_at: '2026-10-01T10:00:00Z', onboarded: true,
        known_topics: [{ id: 'git_basics', name: 'Git Basics' }],
      }),
      domainSummary({
        completed_topics: 1, progress_percent: 3.3, suggested: true,
        known_topics: [{ id: 'git_basics', name: 'Git Basics' }],
        ready_topics: [{ id: 'github_collaboration', name: 'GitHub Collaboration' }],
      }),
    ],
  }
}

/** A /home response for a learner set up in two domains that share Git Basics. Override any part. */
export function home(overrides = {}) {
  const base = {
    domains: [
      {
        ...domainSummary({
          id: 'foundations', name: 'Foundations', total_topics: 3, completed_topics: 1, progress_percent: 33.3,
          joined: true, joined_at: '2026-10-01T10:00:00Z', onboarded: true,
        }),
        up_next: {
          id: 'command_line', name: 'Command Line', description: 'Working in a terminal.', difficulty: 1,
          status: 'unlocked', mastery: 10, prerequisites: [], prerequisite_names: [],
        },
      },
      {
        ...domainSummary({
          completed_topics: 1, progress_percent: 3.3, joined: true, joined_at: '2026-10-02T10:00:00Z', onboarded: true,
        }),
        up_next: {
          id: 'html_basics', name: 'HTML Basics', description: 'Structuring pages.', difficulty: 1,
          status: 'unlocked', mastery: 10, prerequisites: [], prerequisite_names: [],
        },
      },
    ],
    up_next: [
      {
        id: 'command_line', name: 'Command Line', description: 'Working in a terminal.', difficulty: 1,
        status: 'unlocked', mastery: 10, prerequisites: [], prerequisite_names: [], domains: ['foundations'],
      },
      {
        id: 'git_basics', name: 'Git Basics', description: 'Version control with Git.', difficulty: 1,
        status: 'in_progress', mastery: 40, prerequisites: ['command_line'], prerequisite_names: ['Command Line'],
        domains: ['foundations', 'web-development'],
      },
      {
        id: 'html_basics', name: 'HTML Basics', description: 'Structuring pages.', difficulty: 1,
        status: 'unlocked', mastery: 10, prerequisites: [], prerequisite_names: [], domains: ['web-development'],
      },
    ],
    suggestions: [],
    recent_attempts: [
      {
        id: 3, topic_id: 'git_basics', topic_name: 'Git Basics', score: 1, total: 3, passed: false,
        mastery_before: 42, mastery_after: 40, created_at: minutesAgo(2), counted: true,
        integrity_verdict: 'verified', integrity_score: 100,
      },
    ],
  }
  return { ...base, ...overrides }
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
