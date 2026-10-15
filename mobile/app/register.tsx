import { Stack, useRouter } from 'expo-router'
import { useState } from 'react'
import { View } from 'react-native'
import { useAuth } from '@/auth/AuthContext'
import { ApiError } from '@/lib/api'
import { Button, ErrorNote, Field, Screen } from '@/ui/kit'

export default function Register() {
  const { register } = useAuth()
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  async function submit() {
    setBusy(true); setErrors([])
    try { await register(email.trim(), password, name.trim() || undefined); router.replace('/') }
    catch (e) { setErrors(e instanceof ApiError ? [e.message, ...e.details] : ['Something went wrong.']) }
    finally { setBusy(false) }
  }
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Create account' }} />
      <Field label="Name (optional)" value={name} onChangeText={setName} autoComplete="name" />
      <Field label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" autoComplete="email" keyboardType="email-address" />
      <Field label="Password (at least 10 characters)" value={password} onChangeText={setPassword} secureTextEntry autoComplete="new-password" />
      <View>{errors.map((m) => <ErrorNote key={m} message={m} />)}</View>
      <Button title={busy ? 'Creating…' : 'Create account'} disabled={busy || !email || password.length < 10} onPress={() => void submit()} />
    </Screen>
  )
}
