import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, Stack, useLocalSearchParams } from 'expo-router'
import { View } from 'react-native'
import { useAuth } from '@/auth/AuthContext'
import { api } from '@/lib/api'
import type { PathDetail } from '@/lib/types'
import { Async, Button, Card, H1, P, Screen } from '@/ui/kit'

export default function PathScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>()
  const { status } = useAuth()
  const qc = useQueryClient()
  const authed = status === 'authenticated'
  const q = useQuery({ queryKey: ['path', slug, authed], queryFn: () => api<PathDetail>(`/learning/paths/${slug}`, { auth: authed }) })
  const save = useMutation({
    mutationFn: (position: number) => api(`/learning/paths/${slug}/progress`, { method: 'PUT', auth: true, json: { last_item_position: position } }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['path', slug] }),
  })
  return (
    <Screen>
      <Stack.Screen options={{ title: q.data?.title ?? 'Path' }} />
      <Async query={q}>
        {(p) => (
          <>
            <H1>{p.title}</H1>
            {p.description ? <P>{p.description}</P> : null}
            {p.completed ? <P>You have completed this path.</P> : null}
            {p.items.map((it) => (
              <Card key={it.position}>
                <P>{it.position}. {it.title}{it.position <= p.last_item_position ? ' ✓' : ''}</P>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  {it.quiz_id ? <Link href={`/learning/quiz/${it.quiz_id}`} asChild><Button variant="secondary" title="Take quiz" onPress={() => undefined} /></Link> : null}
                  {authed && it.position > p.last_item_position ? <Button variant="secondary" title="Mark done" disabled={save.isPending} onPress={() => save.mutate(it.position)} /> : null}
                </View>
              </Card>
            ))}
            {!authed ? <P small>Log in to save your progress.</P> : null}
          </>
        )}
      </Async>
    </Screen>
  )
}
