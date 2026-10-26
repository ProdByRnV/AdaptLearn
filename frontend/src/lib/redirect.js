const PUBLIC_PATHS = ['/login', '/register']

/** Where to go after signing in: the protected page the learner was sent away from, or the dashboard. */
export function redirectTarget(from) {
  const path = from?.pathname
  if (!path || PUBLIC_PATHS.includes(path)) return '/dashboard'
  return `${path}${from.search ?? ''}${from.hash ?? ''}`
}
