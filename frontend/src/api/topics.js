import api from './client'

/**
 * A domain's topics with the learner's status and their prerequisite ids, sorted by difficulty then
 * name. Prerequisites from other domains are listed per topic in `external_prerequisites`.
 * @returns {Promise<{domain: string, domain_name: string, nodes: object[], links: {source: string, target: string}[]}>}
 */
export async function fetchTopicGraph(domain) {
  const { data } = await api.get('/topics/graph', { params: { domain } })
  return data
}

/**
 * Every topic in every domain, each once, with every prerequisite as a link (the whole map).
 * @returns {Promise<{domains: {id: string, name: string}[], nodes: object[], links: {source: string, target: string}[]}>}
 */
export async function fetchTopicMap() {
  const { data } = await api.get('/topics/map')
  return data
}

/**
 * Onboarding for one domain: mark topics as already known. The server also marks their
 * prerequisites (from any domain), and records that the learner has onboarded in this domain.
 * @returns {Promise<{message: string, known_count: number, added_prerequisites: string[], recommended: object[]}>}
 */
export async function markKnownTopics(domain, topicIds) {
  const { data } = await api.post('/topics/mark-known', { domain, topic_ids: topicIds })
  return data
}
