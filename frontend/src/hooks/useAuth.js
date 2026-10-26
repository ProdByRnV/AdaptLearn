import { useContext } from 'react'

import { AuthContext } from '@/context/auth-context'

/**
 * @returns {{
 *   user: {id: number, username: string, email: string} | null,
 *   token: string | null,
 *   loading: boolean,
 *   isAuthenticated: boolean,
 *   sessionExpired: boolean,
 *   bootError: string | null,
 *   register: (fields: {username: string, email: string, password: string}) => Promise<object>,
 *   login: (fields: {email: string, password: string}) => Promise<object>,
 *   logout: () => void,
 *   refreshUser: () => Promise<void>,
 * }}
 */
export function useAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
