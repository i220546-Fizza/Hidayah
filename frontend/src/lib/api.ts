/**
 * Small API client for the Hidayah backend.
 *
 * The access token lives only in this module's memory (never localStorage), so a script
 * injected into the page cannot read it from storage. The long-lived refresh token is an
 * HttpOnly cookie that JavaScript cannot see; it is only ever sent to /auth/*.
 */
const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  status: number
  details: string[]

  constructor(status: number, message: string, details: string[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function hasAccessToken() {
  return accessToken !== null
}

type RequestOptions = Omit<RequestInit, 'body'> & { json?: unknown; raw?: Blob; auth?: boolean }

async function rawRequest(path: string, { json, raw, auth = false, headers, ...init }: RequestOptions) {
  const h = new Headers(headers)
  h.set('X-Hidayah-Client', 'web') // tells the server to use the cookie flow
  if (json !== undefined) h.set('Content-Type', 'application/json')
  if (raw !== undefined) h.set('Content-Type', 'application/octet-stream')
  if (auth && accessToken) h.set('Authorization', `Bearer ${accessToken}`)
  try {
    return await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: h,
      body: raw !== undefined ? raw : json !== undefined ? JSON.stringify(json) : undefined,
      credentials: 'include',
    })
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
    /* empty or non-JSON body */
  }
  if (!res.ok) {
    const body = (data ?? {}) as { detail?: unknown; errors?: unknown }
    const message = typeof body.detail === 'string' ? body.detail : 'Something went wrong. Try again.'
    const details = Array.isArray(body.errors) ? body.errors.filter((e): e is string => typeof e === 'string') : []
    throw new ApiError(res.status, message, details)
  }
  return data as T
}

// Refresh tokens rotate: using one twice at the same time looks like theft and ends the
// session. So only one refresh may be in flight, and everyone waits for the same result.
let refreshInFlight: Promise<boolean> | null = null

export function refreshSession(): Promise<boolean> {
  refreshInFlight ??= (async () => {
    try {
      const res = await rawRequest('/auth/refresh', { method: 'POST' })
      if (!res.ok) {
        accessToken = null
        return false
      }
      accessToken = ((await res.json()) as { access_token: string }).access_token
      return true
    } catch {
      return false
    } finally {
      refreshInFlight = null
    }
  })()
  return refreshInFlight
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let res = await rawRequest(path, options)
  if (res.status === 401 && options.auth && (await refreshSession())) {
    res = await rawRequest(path, options) // retry once with the new token
  }
  return parse<T>(res)
}
