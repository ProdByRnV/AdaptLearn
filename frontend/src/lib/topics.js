// Display helpers for curriculum data from the API.

export const DIFFICULTY_LABELS = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced', 4: 'Expert' }

export function difficultyLabel(level) {
  return DIFFICULTY_LABELS[level] ?? `Level ${level}`
}

const DOMAIN_NAMES = { 'web-development': 'Web Development' }

/** A readable name from a domain's slug ("web-development"), for when the API's name isn't loaded yet. */
export function domainLabel(slug = '') {
  return DOMAIN_NAMES[slug] ?? slug.split('-').filter(Boolean).map((w) => w[0].toUpperCase() + w.slice(1)).join(' ')
}

/** Topics grouped by difficulty, lowest first, keeping the API's order inside each group. */
export function groupByDifficulty(topics) {
  const groups = new Map()
  for (const topic of topics) {
    if (!groups.has(topic.difficulty)) groups.set(topic.difficulty, [])
    groups.get(topic.difficulty).push(topic)
  }
  return [...groups.entries()].sort(([a], [b]) => a - b).map(([level, items]) => ({ level, topics: items }))
}

/**
 * Prerequisites that come with the selection: every topic needed (directly or further back) by a
 * selected topic, mapped to the selected topics that need it. Mirrors the server, which marks the
 * prerequisites of known topics as known too. Selected topics and those in `exclude` are left out.
 *
 * @param {Map<string, {prerequisites: string[]}>} topicsById
 * @param {Iterable<string>} selected
 * @param {Set<string>} [exclude]
 * @returns {Map<string, string[]>} implied topic id -> ids of the selected topics that need it
 */
export function impliedPrerequisites(topicsById, selected, exclude = new Set()) {
  const chosen = new Set(selected)
  const implied = new Map()
  for (const start of chosen) {
    const seen = new Set()
    const stack = [...(topicsById.get(start)?.prerequisites ?? [])]
    while (stack.length) {
      const id = stack.pop()
      if (seen.has(id)) continue
      seen.add(id)
      stack.push(...(topicsById.get(id)?.prerequisites ?? []))
      if (chosen.has(id) || exclude.has(id)) continue
      if (!implied.has(id)) implied.set(id, [])
      implied.get(id).push(start)
    }
  }
  return implied
}

/**
 * The primary action for a topic the learner can study (PRD 9: Start Topic / Continue / Retry Quiz).
 * `retry` is true when the learner's latest quiz on it failed or the topic needs attention.
 */
export function topicAction(topic, { retry = false } = {}) {
  const to = `/quiz/${encodeURIComponent(topic.id)}`
  if (topic.status === 'completed') return { label: 'Practise again', to }
  if (retry) return { label: 'Retry quiz', to }
  if (topic.status === 'in_progress') return { label: 'Continue', to }
  return { label: 'Start topic', to }
}

/**
 * Topics whose next action is "Retry quiz": the learner's latest counted attempt on them failed,
 * or they need attention. `attempts` are newest first.
 */
export function retryTopicIds(attempts, attention = []) {
  const ids = new Set(attention.map((t) => t.id))
  const seen = new Set()
  for (const attempt of attempts) {
    if (!attempt.counted || seen.has(attempt.topic_id)) continue
    seen.add(attempt.topic_id)
    if (!attempt.passed) ids.add(attempt.topic_id)
  }
  return ids
}

/** "A", "A and B", "A, B and C" (up to `max` names), "A, B and 2 more" */
export function listNames(names, max = 2) {
  if (names.length <= 1) return names.join('')
  if (names.length <= max) return `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`
  return `${names.slice(0, max).join(', ')} and ${names.length - max} more`
}
