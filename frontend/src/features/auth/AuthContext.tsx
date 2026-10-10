import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, refreshSession, setAccessToken } from '@/lib/api'
import type { AuthStatus, User } from './types'

export type AuthContextValue = {
  status: AuthStatus
  user: User | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

type TokenResponse = { access_token: string }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)

  const loadUser = useCallback(async () => {
    const me = await api<User>('/users/me', { auth: true })
    setUser(me)
    setStatus('authenticated')
  }, [])

  // On first load, try to continue an existing session using the refresh cookie.
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (await refreshSession()) await loadUser()
        else if (!cancelled) setStatus('anonymous')
      } catch {
        if (!cancelled) setStatus('anonymous')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api<TokenResponse>('/auth/login', { method: 'POST', json: { email, password } })
      setAccessToken(tokens.access_token)
      await loadUser()
    },
    [loadUser],
  )

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      await api('/auth/register', {
        method: 'POST',
        json: { email, password, display_name: displayName || null },
      })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    try {
      await api('/auth/logout', { method: 'POST' })
    } catch {
      // The server could not be told. That must not trap the person in a
      // signed-in screen, so we still forget the session on this device.
    } finally {
      setAccessToken(null)
      setUser(null)
      setStatus('anonymous')
    }
  }, [])

  const value = useMemo(() => ({ status, user, login, register, logout }), [status, user, login, register, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
