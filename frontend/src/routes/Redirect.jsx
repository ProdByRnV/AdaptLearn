import { Navigate, useLocation } from 'react-router'

/** Replace an old address with its new one, optionally keeping the query (e.g. ?topic=). */
export function Redirect({ to, keepQuery = false }) {
  const { search } = useLocation()
  return <Navigate to={keepQuery ? `${to}${search}` : to} replace />
}
