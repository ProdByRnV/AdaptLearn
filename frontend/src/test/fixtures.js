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
