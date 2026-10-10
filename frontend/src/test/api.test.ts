import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

function jsonResponse(status: number, body?: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// api.ts keeps the access token and refresh state in module memory, so load a fresh copy per test.
async function loadApi() {
  vi.resetModules()
  return import('@/lib/api')
}

describe('api client', () => {
  const fetchMock = vi.fn()
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends the web client header and includes cookies', async () => {
    const { api } = await loadApi()
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }))
    await api('/health')
    const [, init] = fetchMock.mock.calls[0]
    expect(new Headers(init.headers).get('X-Hidayah-Client')).toBe('web')
    expect(init.credentials).toBe('include')
  })

  it('attaches the bearer token only to authenticated calls', async () => {
    const { api, setAccessToken } = await loadApi()
    setAccessToken('tok123')
    fetchMock.mockResolvedValue(jsonResponse(200, {}))
    await api('/public')
    await api('/private', { auth: true })
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get('Authorization')).toBeNull()
    expect(new Headers(fetchMock.mock.calls[1][1].headers).get('Authorization')).toBe('Bearer tok123')
  })

  it('never stores tokens in browser storage', async () => {
    const { api, setAccessToken } = await loadApi()
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    setAccessToken('secret-token')
    fetchMock.mockResolvedValue(jsonResponse(200, {}))
    await api('/x', { auth: true })
    expect(setItem).not.toHaveBeenCalled()
    expect(JSON.stringify({ ...localStorage })).not.toContain('secret-token')
    expect(JSON.stringify({ ...sessionStorage })).not.toContain('secret-token')
  })

  it('sends only ONE refresh request when several happen at once', async () => {
    const { refreshSession } = await loadApi()
    fetchMock.mockResolvedValue(jsonResponse(200, { access_token: 'new' }))
    const results = await Promise.all([refreshSession(), refreshSession(), refreshSession()])
    expect(results).toEqual([true, true, true])
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('refreshes and retries once when a call returns 401', async () => {
    const { api, setAccessToken } = await loadApi()
    setAccessToken('expired')
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Sign in again to continue.' }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'fresh' })) // /auth/refresh
      .mockResolvedValueOnce(jsonResponse(200, { email: 'a@example.com' }))
    const me = await api<{ email: string }>('/users/me', { auth: true })
    expect(me.email).toBe('a@example.com')
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('Authorization')).toBe('Bearer fresh')
  })

  it('throws ApiError with the server message and detail list', async () => {
    const { api, ApiError } = await loadApi()
    fetchMock.mockResolvedValue(jsonResponse(422, { detail: 'Choose a stronger password.', errors: ['Use at least 10 characters.'] }))
    await expect(api('/auth/register', { method: 'POST', json: {} })).rejects.toMatchObject({
      status: 422,
      message: 'Choose a stronger password.',
      details: ['Use at least 10 characters.'],
    })
    expect(new ApiError(1, 'x')).toBeInstanceOf(Error)
  })

  it('turns network failures into a friendly ApiError', async () => {
    const { api } = await loadApi()
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(api('/health')).rejects.toMatchObject({ status: 0, message: expect.stringMatching(/could not reach the server/i) })
  })

  it('handles 204 responses', async () => {
    const { api } = await loadApi()
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))
    await expect(api('/auth/logout', { method: 'POST' })).resolves.toBeUndefined()
  })
})
