import api from './client'

/** @returns {Promise<{access_token: string, token_type: 'bearer', user: {id: number, username: string, email: string}}>} */
export async function registerRequest({ username, email, password }) {
  const { data } = await api.post('/auth/register', { username, email, password })
  return data
}

/** @returns {Promise<{access_token: string, token_type: 'bearer', user: {id: number, username: string, email: string}}>} */
export async function loginRequest({ email, password }) {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

/** @returns {Promise<{id: number, username: string, email: string}>} */
export async function fetchCurrentUser() {
  const { data } = await api.get('/auth/me')
  return data
}
