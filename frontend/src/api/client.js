import axios from 'axios'

export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/+$/, '')

const TOKEN_KEY = 'adaptlearn.token'

// localStorage can throw (private mode, blocked site data); treat that as "no token".
export const tokenStorage = {
  key: TOKEN_KEY,
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      // The session still works for this tab; it just won't survive a reload.
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      // Nothing stored, nothing to clear.
    }
  },
}

const api = axios.create({
  baseURL: API_URL,
  timeout: 15_000,
})

let unauthorizedHandler = null

/** Register the callback run when the server rejects the current session. Returns an unsubscribe function. */
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
  return () => {
    if (unauthorizedHandler === handler) unauthorizedHandler = null
  }
}

api.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token && !config.headers.has('Authorization')) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // A 401 on a request that carried the current token means the session is over (expired token,
    // deleted account). A 401 without a token is an ordinary failure, such as a wrong password, and
    // is left to the caller. A 401 for a token that has since been replaced is stale and ignored.
    const sent = error.config?.headers?.get?.('Authorization')
    const current = tokenStorage.get()
    if (error.response?.status === 401 && sent && current && sent === `Bearer ${current}`) {
      unauthorizedHandler?.()
    }
    return Promise.reject(error)
  },
)

const NETWORK_ERROR = "Can't reach the AdaptLearn server. Check your connection and try again."
const TIMEOUT_ERROR = 'The server took too long to respond. Please try again.'
const GENERIC_ERROR = 'Something went wrong. Please try again.'

/** A message fit to show the learner. The backend always answers errors with {"detail": "..."}. */
export function getErrorMessage(error, fallback = GENERIC_ERROR) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') return TIMEOUT_ERROR
  if (error?.isAxiosError && !error.response) return NETWORK_ERROR
  return fallback
}

/** Seconds from a 429 response's Retry-After header, or null. */
export function getRetryAfterSeconds(error) {
  if (error?.response?.status !== 429) return null
  const seconds = Number.parseInt(error.response.headers?.['retry-after'], 10)
  return Number.isFinite(seconds) && seconds >= 0 ? seconds : null
}

export default api
