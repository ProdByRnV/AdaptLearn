const NOT_REMEMBERED = ['/', '/login', '/register']

/**
 * The protected page a learner was sent away from (path, query and hash), or null when there is
 * nothing worth returning to and the app should choose between onboarding and the dashboard.
 */
export function rememberedTarget(from) {
  const path = from?.pathname
  if (!path || NOT_REMEMBERED.includes(path)) return null
  return `${path}${from.search ?? ''}${from.hash ?? ''}`
}
