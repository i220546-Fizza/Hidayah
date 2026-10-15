import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Stack } from 'expo-router'
import { useState } from 'react'
import { Alert } from 'react-native'
import { useAuth } from '@/auth/AuthContext'
import { ApiError, api } from '@/lib/api'
import { Async, Button, Card, ErrorNote, Field, H2, P, Screen } from '@/ui/kit'

type Conversation = { id: string; title: string | null }

export default function Account() {
  const { user, logout } = useAuth()
  const qc = useQueryClient()
  const convs = useQuery({ queryKey: ['conversations'], queryFn: () => api<Conversation[]>('/ask/conversations', { auth: true }), enabled: !!user })
  const del = useMutation({
    mutationFn: (id: string) => api(`/ask/conversations/${id}`, { method: 'DELETE', auth: true }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['conversations'] }),
  })
  const [password, setPassword] = useState('')
  const [confirming, setConfirming] = useState(false)
  const remove = useMutation({
    mutationFn: () => api('/users/me/delete', { method: 'POST', auth: true, json: { password } }),
    onSuccess: () => void logout(),
  })
  const exportData = useMutation({
    mutationFn: () => api<unknown>('/users/me/export', { auth: true }),
    onSuccess: (d) => Alert.alert('Your data', JSON.stringify(d, null, 2).slice(0, 1500)),
  })
  if (!user) return <Screen><P>Please log in.</P></Screen>
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Your account' }} />
      <P>{user.display_name ? `${user.display_name} · ` : ''}{user.email}</P>
      <H2>Your questions</H2>
      <Async query={convs}>
        {(items) => items.length === 0 ? <P>You have not asked anything yet.</P> : items.map((c) => (
          <Card key={c.id}><P>{c.title ?? 'Conversation'}</P><Button variant="secondary" title="Delete" onPress={() => del.mutate(c.id)} /></Card>
        ))}
      </Async>
      <H2>Your data</H2>
      <Button variant="secondary" title="Show my data" onPress={() => exportData.mutate()} />
      <P small>The website offers a full download as a file.</P>
      <H2>Delete account</H2>
      <P small>This permanently removes your account and everything linked to it.</P>
      {!confirming ? <Button variant="secondary" title="Delete my account…" onPress={() => setConfirming(true)} /> : (
        <>
          <Field label="Confirm with your password" value={password} onChangeText={setPassword} secureTextEntry />
          {remove.error ? <ErrorNote message={remove.error instanceof ApiError ? remove.error.message : 'Something went wrong.'} /> : null}
          <Button title="Permanently delete" disabled={!password || remove.isPending} onPress={() => remove.mutate()} />
        </>
      )}
    </Screen>
  )
}
