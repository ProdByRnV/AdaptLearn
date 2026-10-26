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
