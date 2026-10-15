import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Async } from '@/components/content/Async'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { useAuth } from '@/features/auth/useAuth'
import { ApiError, api } from '@/lib/api'
import type { Bookmark, Page } from '@/lib/types'

type Conversation = { id: string; title: string | null; created_at: string }

const bookmarkLink = (b: Bookmark) => (b.type === 'hadith' ? `/hadith/${b.target_id}` : b.type === 'dua' ? '/duas' : '/quran')

function VerifyBanner() {
  const [state, setState] = useState<'idle' | 'sent' | 'error'>('idle')
  async function resend() {
    try {
      await api('/auth/request-verification', { method: 'POST', auth: true })
      setState('sent')
    } catch {
      setState('error')
    }
  }
  return (
    <div className="mt-4 rounded-md border border-bronze bg-white p-3 text-sm" role="status">
      Your email is not confirmed yet.{' '}
      {state === 'sent' ? 'A new link was sent.' : state === 'error' ? 'Could not send the link; try again later.' : (
        <button type="button" className="text-emerald underline" onClick={() => void resend()}>Send me a confirmation link</button>
      )}
    </div>
  )
}

export function AccountPage() {
  const { user, logout } = useAuth()
  const qc = useQueryClient()
  const convs = useQuery({ queryKey: ['conversations'], queryFn: () => api<Conversation[]>('/ask/conversations', { auth: true }) })
  const marks = useQuery({ queryKey: ['bookmarks'], queryFn: () => api<Page<Bookmark>>('/bookmarks', { auth: true }) })
  const delConv = useMutation({
    mutationFn: (id: string) => api(`/ask/conversations/${id}`, { method: 'DELETE', auth: true }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['conversations'] }),
  })
  const delMark = useMutation({
    mutationFn: (id: number) => api(`/bookmarks/${id}`, { method: 'DELETE', auth: true }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['bookmarks'] }),
  })
  const [exportError, setExportError] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirming, setConfirming] = useState(false)
  const del = useMutation({
    mutationFn: () => api('/users/me/delete', { method: 'POST', auth: true, json: { password } }),
    onSuccess: () => void logout(),
  })

  async function download() {
    setExportError(null)
    try {
      const data = await api<unknown>('/users/me/export', { auth: true })
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'hidayah-my-data.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setExportError(e instanceof ApiError ? e.message : 'Could not download your data.')
    }
  }

  return (
    <Container className="max-w-3xl py-12">
      <h1 className="text-3xl sm:text-4xl">Your account</h1>
      <p className="mt-2">{user?.display_name ? `${user.display_name} · ` : ''}{user?.email}</p>
      {user && !user.email_verified && <VerifyBanner />}
      {user?.roles.includes('admin') && <p className="mt-2"><Link className="text-emerald underline" to="/admin">Open the admin dashboard</Link></p>}

      <h2 className="mt-10 text-2xl">Bookmarks</h2>
      <div className="mt-3">
        <Async query={marks}>
          {(p) => p.items.length === 0 ? <p>No bookmarks yet.</p> : (
            <ul className="space-y-2">
              {p.items.map((b) => (
                <li key={b.id} className="flex items-center justify-between rounded-md border border-sand bg-white px-4 py-2">
                  <Link className="underline" to={bookmarkLink(b)}>{b.type} #{b.target_id}</Link>
                  <Button variant="quiet" onClick={() => delMark.mutate(b.id)} aria-label={`Remove ${b.type} bookmark ${b.target_id}`}>Remove</Button>
                </li>
              ))}
            </ul>
          )}
        </Async>
      </div>

      <h2 className="mt-10 text-2xl">Your questions</h2>
      <div className="mt-3">
        <Async query={convs}>
          {(items) => items.length === 0 ? <p>You have not asked anything yet.</p> : (
            <ul className="space-y-2">
              {items.map((c) => (
                <li key={c.id} className="flex items-center justify-between rounded-md border border-sand bg-white px-4 py-2">
                  <span className="truncate">{c.title ?? 'Conversation'}</span>
                  <Button variant="quiet" onClick={() => delConv.mutate(c.id)} aria-label={`Delete conversation ${c.title ?? ''}`}>Delete</Button>
                </li>
              ))}
            </ul>
          )}
        </Async>
      </div>

      <h2 className="mt-10 text-2xl">Your data</h2>
      <Card className="mt-3 space-y-3">
        <p className="text-sm">Download everything we hold about you as a file.</p>
        <Button variant="secondary" onClick={() => void download()}>Download my data</Button>
        {exportError && <FormError title={exportError} />}
      </Card>

      <h2 className="mt-10 text-2xl">Delete account</h2>
      <Card className="mt-3 space-y-3">
        <p className="text-sm">This permanently removes your account and everything linked to it. It cannot be undone.</p>
        {!confirming ? (
          <Button variant="secondary" onClick={() => setConfirming(true)}>Delete my account…</Button>
        ) : (
          <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); del.mutate() }}>
            <TextField label="Confirm with your password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            {del.error && <FormError title={del.error instanceof ApiError ? del.error.message : 'Something went wrong.'} />}
            <Button type="submit" disabled={!password || del.isPending}>Permanently delete</Button>
          </form>
        )}
      </Card>
    </Container>
  )
}
