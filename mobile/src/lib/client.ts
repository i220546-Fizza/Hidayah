/**
 * API client for the mobile app.
 *
 * The refresh token is kept in the device's secure storage (Keychain / Keystore) and sent in the
 * JSON body, because a phone has no browser cookie. The short-lived access token lives only in
 * memory. Storage and fetch are passed in so the logic can be tested without a phone.
 */
export class ApiError extends Error {
  constructor(public status: number, message: string, public details: string[] = []) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface TokenStorage {
  get(): Promise<string | null>
  set(token: string): Promise<void>
  clear(): Promise<void>
}

type Opts = { method?: string; json?: unknown; auth?: boolean }

export function createClient(baseUrl: string, storage: TokenStorage, fetchImpl: typeof fetch = fetch) {
  let accessToken: string | null = null
  let refreshing: Promise<boolean> | null = null

  async function send(path: string, { method = 'GET', json, auth }: Opts) {
    const headers: Record<string, string> = {}
    if (json !== undefined) headers['Content-Type'] = 'application/json'
    if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`
    try {
      return await fetchImpl(`${baseUrl}${path}`, { method, headers, body: json !== undefined ? JSON.stringify(json) : undefined })
    } catch {
      throw new ApiError(0, 'Could not reach the server. Check your connection and try again.')
    }
  }

  async function parse<T>(res: Response): Promise<T> {
    if (res.status === 204) return undefined as T
    let data: unknown = null
    try {
      data = await res.json()
    } catch {
      /* empty body */
    }
    if (!res.ok) {
      const b = (data ?? {}) as { detail?: unknown; errors?: unknown }
      throw new ApiError(
        res.status,
        typeof b.detail === 'string' ? b.detail : 'Something went wrong. Try again.',
        Array.isArray(b.errors) ? b.errors.filter((e): e is string => typeof e === 'string') : [],
      )
    }
    return data as T
  }

  // Refresh tokens rotate, so two refreshes at once would look like token theft. Share one.
  function refresh(): Promise<boolean> {
    refreshing ??= (async () => {
      try {
        const token = await storage.get()
        if (!token) return false
        const res = await send('/auth/refresh', { method: 'POST', json: { refresh_token: token } })
        if (!res.ok) {
          accessToken = null
          if (res.status === 401) await storage.clear()
          return false
        }
        const body = (await res.json()) as { access_token: string; refresh_token?: string }
        accessToken = body.access_token
        if (body.refresh_token) await storage.set(body.refresh_token)
        return true
      } catch {
        return false
      } finally {
        refreshing = null
      }
    })()
    return refreshing
  }

  async function api<T>(path: string, opts: Opts = {}): Promise<T> {
    let res = await send(path, opts)
    if (res.status === 401 && opts.auth && (await refresh())) res = await send(path, opts)
    return parse<T>(res)
  }

  return {
    api,
    refresh,
    hasSession: () => accessToken !== null,
    async login(email: string, password: string) {
      const body = await api<{ access_token: string; refresh_token?: string }>('/auth/login', { method: 'POST', json: { email, password } })
      if (!body.refresh_token) throw new ApiError(500, 'The server did not return a session.')
      accessToken = body.access_token
      await storage.set(body.refresh_token)
    },
    async logout() {
      const token = await storage.get()
      try {
        if (token) await api('/auth/logout', { method: 'POST', json: { refresh_token: token } })
      } catch {
        /* could not tell the server; we still forget the session on this phone */
      } finally {
        accessToken = null
        await storage.clear()
      }
    },
  }
}
