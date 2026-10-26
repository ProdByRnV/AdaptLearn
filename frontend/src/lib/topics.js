// Display helpers for curriculum data from the API.

export const DIFFICULTY_LABELS = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced', 4: 'Expert' }

export function difficultyLabel(level) {
  return DIFFICULTY_LABELS[level] ?? `Level ${level}`
}

const DOMAIN_NAMES = { 'web-development': 'Web Development' }

/** The API identifies domains by slug ("web-development"); show a readable name. */
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

/** "A", "A and B", "A, B and 2 more" */
export function listNames(names, max = 2) {
  if (names.length <= max) return names.length === 2 ? `${names[0]} and ${names[1]}` : names.join('')
  return `${names.slice(0, max).join(', ')} and ${names.length - max} more`
}
