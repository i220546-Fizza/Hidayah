import { describe, expect, it, vi } from 'vitest'
import { ApiError, createClient, type TokenStorage } from './client'

const res = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function memory(initial: string | null = null): TokenStorage & { value: string | null } {
  const s = {
    value: initial,
    get: async () => s.value,
    set: async (t: string) => { s.value = t },
    clear: async () => { s.value = null },
  }
  return s
}

describe('mobile api client', () => {
  it('login keeps the refresh token in secure storage and uses the access token', async () => {
    const store = memory()
    const f = vi.fn()
      .mockResolvedValueOnce(res(200, { access_token: 'A1', refresh_token: 'R1' }))
      .mockResolvedValueOnce(res(200, { ok: true }))
    const c = createClient('http://x', store, f as never)
    await c.login('a@example.com', 'pw')
    expect(store.value).toBe('R1')
    await c.api('/users/me', { auth: true })
    expect(f.mock.calls[1][1].headers.Authorization).toBe('Bearer A1')
  })

  it('does not send the Authorization header unless asked', async () => {
    const f = vi.fn().mockResolvedValue(res(200, []))
    const c = createClient('http://x', memory(), f as never)
    await c.login('a', 'b').catch(() => undefined)
    await c.api('/surahs')
    expect(JSON.stringify(f.mock.calls.at(-1)![1].headers)).not.toContain('Authorization')
  })

  it('refreshes once on 401, stores the rotated token and retries', async () => {
    const store = memory('R1')
    const f = vi.fn()
      .mockResolvedValueOnce(res(401, { detail: 'Sign in again to continue.' }))
      .mockResolvedValueOnce(res(200, { access_token: 'A2', refresh_token: 'R2' }))
      .mockResolvedValueOnce(res(200, { me: 1 }))
    const c = createClient('http://x', store, f as never)
    expect(await c.api('/users/me', { auth: true })).toEqual({ me: 1 })
    expect(JSON.parse(f.mock.calls[1][1].body)).toEqual({ refresh_token: 'R1' })
    expect(store.value).toBe('R2')
    expect(f.mock.calls[2][1].headers.Authorization).toBe('Bearer A2')
  })

  it('shares one refresh between simultaneous requests', async () => {
    const store = memory('R1')
    let refreshes = 0
    const f = vi.fn(async (url: string) => {
      if (String(url).endsWith('/auth/refresh')) { refreshes++; return res(200, { access_token: 'A2', refresh_token: 'R2' }) }
      return f.mock.calls.filter(([u]) => u === url).length <= 1 ? res(401, {}) : res(200, { ok: 1 })
    })
    const c = createClient('http://x', store, f as never)
    await Promise.all([c.api('/a', { auth: true }), c.api('/b', { auth: true })])
    expect(refreshes).toBe(1)
  })

  it('clears the stored token when the server rejects the refresh token', async () => {
    const store = memory('BAD')
    const f = vi.fn().mockResolvedValue(res(401, { detail: 'Sign in again to continue.' }))
    const c = createClient('http://x', store, f as never)
    await expect(c.api('/users/me', { auth: true })).rejects.toMatchObject({ status: 401 })
    expect(store.value).toBeNull()
  })

  it('keeps the stored token if the refresh failed only because the network is down', async () => {
    const store = memory('R1')
    const f = vi.fn()
      .mockResolvedValueOnce(res(401, {}))
      .mockRejectedValueOnce(new TypeError('offline'))
    const c = createClient('http://x', store, f as never)
    await expect(c.api('/users/me', { auth: true })).rejects.toBeInstanceOf(ApiError)
    expect(store.value).toBe('R1')
  })

  it('logout forgets the session even when the server cannot be reached', async () => {
    const store = memory('R1')
    const f = vi.fn().mockRejectedValue(new TypeError('offline'))
    const c = createClient('http://x', store, f as never)
    await c.logout()
    expect(store.value).toBeNull()
    expect(c.hasSession()).toBe(false)
  })

  it('maps server errors to readable messages and details', async () => {
    const f = vi.fn().mockResolvedValue(res(422, { detail: 'Choose a stronger password.', errors: ['Too short'] }))
    const c = createClient('http://x', memory(), f as never)
    await expect(c.api('/auth/register', { method: 'POST', json: {} })).rejects.toMatchObject({
      status: 422, message: 'Choose a stronger password.', details: ['Too short'],
    })
  })

  it('reports an unreachable server with a friendly message', async () => {
    const f = vi.fn().mockRejectedValue(new TypeError('Network request failed'))
    const c = createClient('http://x', memory(), f as never)
    await expect(c.api('/surahs')).rejects.toMatchObject({ status: 0, message: expect.stringContaining('Could not reach') })
  })
})
