import { useQuery } from '@tanstack/react-query'
import { Stack } from 'expo-router'
import { useState } from 'react'
import { api } from '@/lib/api'
import type { SearchHit } from '@/lib/types'
import { Async, Button, Card, Field, P, Screen, SourceCredit } from '@/ui/kit'

export default function SearchScreen() {
  const [text, setText] = useState('')
  const [term, setTerm] = useState('')
  const q = useQuery({ queryKey: ['search', term], enabled: term.length >= 2, queryFn: () => api<{ hits: SearchHit[]; note: string | null }>(`/search?q=${encodeURIComponent(term)}`) })
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Search' }} />
      <Field label="Search words" value={text} onChangeText={setText} returnKeyType="search" onSubmitEditing={() => setTerm(text.trim())} />
      <Button title="Search" disabled={text.trim().length < 2} onPress={() => setTerm(text.trim())} />
      {term.length >= 2 && (
        <Async query={q}>
          {(r) => r.hits.length === 0 ? <P>{r.note ?? 'No results.'}</P> : r.hits.map((h, i) => (
            <Card key={i}><P small>{h.type.replace('_', ' ')}</P><P>{h.title}</P><P small>{h.snippet}</P><SourceCredit source={h.source} /></Card>
          ))}
        </Async>
      )}
    </Screen>
  )
}
