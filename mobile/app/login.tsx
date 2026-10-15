import { Link, Stack, useRouter } from 'expo-router'
import { useState } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { ApiError } from '@/lib/api'
import { Button, ErrorNote, Field, P, Screen } from '@/ui/kit'

export default function Login() {
  const { login } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  async function submit() {
    setBusy(true); setError(null)
    try { await login(email.trim(), password); router.replace('/') }
    catch (e) { setError(e instanceof ApiError ? e.message : 'Something went wrong.') }
    finally { setBusy(false) }
  }
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Log in' }} />
      <Field label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" autoComplete="email" keyboardType="email-address" textContentType="emailAddress" />
      <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" textContentType="password" />
      {error ? <ErrorNote message={error} /> : null}
      <Button title={busy ? 'Logging in…' : 'Log in'} disabled={busy || !email || !password} onPress={() => void submit()} />
      <Link href="/register"><P>No account? Create one</P></Link>
    </Screen>
  )
}
