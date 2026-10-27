import api from './client'

/**
 * Everything the dashboard shows, in one call: stats, the next 3 topics, topics needing attention
 * (with resources), the 5 latest quiz attempts and mastery for every topic.
 */
export async function fetchDashboard() {
  const { data } = await api.get('/progress/dashboard')
  return data
}
