import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, client } from '@/lib/api'

export type User = { id: string; email: string; display_name: string | null; email_verified: boolean; roles: string[]; created_at: string }
type Status = 'loading' | 'authenticated' | 'anonymous'
type Value = {
  status: Status
  user: User | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
}

const Ctx = createContext<Value | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>('loading')
  const [user, setUser] = useState<User | null>(null)

  const loadUser = useCallback(async () => {
    setUser(await api<User>('/users/me', { auth: true }))
    setStatus('authenticated')
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (await client.refresh()) await loadUser()
        else if (!cancelled) setStatus('anonymous')
      } catch {
        if (!cancelled) setStatus('anonymous')
      }
    })()
    return () => { cancelled = true }
  }, [loadUser])

  const login = useCallback(async (email: string, password: string) => {
    await client.login(email, password)
    await loadUser()
  }, [loadUser])

  const register = useCallback(async (email: string, password: string, name?: string) => {
    await api('/auth/register', { method: 'POST', json: { email, password, display_name: name || null } })
    await login(email, password)
  }, [login])

  const logout = useCallback(async () => {
    await client.logout()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo(() => ({ status, user, login, register, logout }), [status, user, login, register, logout])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth() {
  const v = useContext(Ctx)
  if (!v) throw new Error('useAuth must be used inside AuthProvider')
  return v
}
