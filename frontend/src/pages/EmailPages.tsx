import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { ApiError, api } from '@/lib/api'
import { AuthPageShell } from './AuthPageShell'

const message = (e: unknown) => (e instanceof ApiError ? [e.message, ...e.details].join(' ') : 'Something went wrong. Try again.')

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api('/auth/forgot-password', { method: 'POST', json: { email } })
      setDone(true)
    } catch (err) {
      setError(message(err))
    }
  }
  return (
    <AuthPageShell title="Forgot your password?" intro="Enter your email and we will send a link to choose a new one.">
      {done ? (
        <p role="status">If an account exists for that address, a reset link is on its way. It works once and expires in a couple of hours.</p>
      ) : (
        <form onSubmit={(e) => void submit(e)} className="space-y-5">
          {error && <FormError title={error} />}
          <TextField label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button type="submit" className="w-full" disabled={!email}>Send reset link</Button>
        </form>
      )}
      <p className="mt-5 text-sm"><Link to="/login" className="text-emerald underline">Back to log in</Link></p>
    </AuthPageShell>
  )
}

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [pw, setPw] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api('/auth/reset-password', { method: 'POST', json: { token, new_password: pw } })
      setDone(true)
    } catch (err) {
      setError(message(err))
    }
  }
  return (
    <AuthPageShell title="Choose a new password" intro="Use at least 10 characters. You will be signed out on all devices.">
      {!token ? (
        <FormError title="This link is incomplete. Please use the link from your email." />
      ) : done ? (
        <p role="status">Your password was changed. <Link to="/login" className="text-emerald underline">Log in</Link></p>
      ) : (
        <form onSubmit={(e) => void submit(e)} className="space-y-5">
          {error && <FormError title={error} />}
          <TextField label="New password" type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} />
          <Button type="submit" className="w-full" disabled={pw.length < 10}>Change password</Button>
        </form>
      )}
    </AuthPageShell>
  )
}

export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [state, setState] = useState<'working' | 'ok' | 'bad'>(token ? 'working' : 'bad')
  const [error, setError] = useState<string | null>(token ? null : 'This link is incomplete. Please use the link from your email.')
  useEffect(() => {
    if (!token) return
    let cancelled = false
    api('/auth/verify-email', { method: 'POST', json: { token } })
      .then(() => !cancelled && setState('ok'))
      .catch((e) => { if (!cancelled) { setState('bad'); setError(message(e)) } })
    return () => { cancelled = true }
  }, [token])
  return (
    <AuthPageShell title="Confirm your email" intro="One moment while we check your link.">
      {state === 'working' && <p role="status">Checking…</p>}
      {state === 'ok' && <p role="status">Your email is confirmed. Thank you. <Link to="/" className="text-emerald underline">Go home</Link></p>}
      {state === 'bad' && <FormError title={error ?? 'This link is not valid.'} />}
    </AuthPageShell>
  )
}
