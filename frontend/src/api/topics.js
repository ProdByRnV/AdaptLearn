import api from './client'

/** @returns {Promise<{domain: string, onboarded: boolean, curriculum_complete: boolean, recommended: object[]}>} */
export async function fetchLearningPath() {
  const { data } = await api.get('/topics/learning-path')
  return data
}
