import api from './client'

/**
 * Everything a domain's dashboard shows, in one call: stats, the next 3 topics, topics needing
 * attention (with resources), the domain's 5 latest quiz attempts and mastery for every topic.
 */
export async function fetchDashboard(domain) {
  const { data } = await api.get('/progress/dashboard', { params: { domain } })
  return data
}
