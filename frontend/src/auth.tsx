import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { get, getToken, post, setToken } from './api'
import type { Role, User } from './types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  can: (...roles: Role[]) => boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => getToken() !== null)

  useEffect(() => {
    if (!getToken()) return
    get<User>('/auth/me')
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const onLogout = () => setUser(null)
    window.addEventListener('reqtrace:logout', onLogout)
    return () => window.removeEventListener('reqtrace:logout', onLogout)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const result = await post<{ access_token: string; user: User }>('/auth/login', { email, password })
    setToken(result.access_token)
    setUser(result.user)
  }, [])

  const logout = useCallback(async () => {
    try {
      await post('/auth/logout')
    } finally {
      setToken(null)
      setUser(null)
    }
  }, [])

  const can = useCallback((...roles: Role[]) => !!user && roles.includes(user.role), [user])

  return <AuthContext.Provider value={{ user, loading, login, logout, can }}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
