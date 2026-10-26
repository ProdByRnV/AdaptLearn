import api from './client'

/** @returns {Promise<{domain: string, onboarded: boolean, curriculum_complete: boolean, recommended: object[]}>} */
export async function fetchLearningPath() {
  const { data } = await api.get('/topics/learning-path')
  return data
}

/**
 * Every topic with the learner's status and its prerequisite ids, sorted by difficulty then name.
 * @returns {Promise<{domain: string, nodes: object[], links: {source: string, target: string}[]}>}
 */
export async function fetchTopicGraph() {
  const { data } = await api.get('/topics/graph')
  return data
}

/**
 * Onboarding: mark topics as already known. The server also marks their prerequisites.
 * @returns {Promise<{message: string, known_count: number, added_prerequisites: string[], recommended: object[]}>}
 */
export async function markKnownTopics(topicIds) {
  const { data } = await api.post('/topics/mark-known', { topic_ids: topicIds })
  return data
}
