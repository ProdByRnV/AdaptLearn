import api from './client'

// Domains (backend Phase 23). Progress belongs to topics, so a topic shared by several domains
// counts in each of them; joining a domain only records that the learner wants to study it.

/**
 * Every domain, in curriculum order, with the learner's standing in it.
 * @returns {Promise<{domains: {id: string, name: string, description: string, total_topics: number,
 *   completed_topics: number, in_progress_topics: number, available_topics: number, progress_percent: number,
 *   curriculum_complete: boolean, joined: boolean, joined_at: string|null, onboarded: boolean,
 *   known_topics: {id: string, name: string}[], ready_topics: {id: string, name: string}[], suggested: boolean}[]}>}
 */
export async function fetchCatalogue() {
  const { data } = await api.get('/domains')
  return data
}

/** Join a domain. Joining again changes nothing. @returns {Promise<{domain: string, domain_name: string, joined_at: string, onboarded: boolean}>} */
export async function joinDomain(domainId) {
  const { data } = await api.post(`/domains/${encodeURIComponent(domainId)}/join`)
  return data
}

/**
 * The home page in one call: joined domains (each with its next topic), the next topics across
 * them, suggested domains and the latest quizzes from any domain.
 */
export async function fetchHome() {
  const { data } = await api.get('/home')
  return data
}
