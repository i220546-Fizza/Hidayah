import { useMutation } from '@tanstack/react-query'
import { Link } from 'expo-router'
import { useState } from 'react'
import { View } from 'react-native'
import { useAuth } from '@/auth/AuthContext'
import { ApiError, api } from '@/lib/api'
import type { AskResponse, ChatMessage } from '@/lib/types'
import { Arabic, Button, Card, ErrorNote, Field, H2, P, Screen, SourceCredit } from '@/ui/kit'

function Answer({ m }: { m: ChatMessage }) {
  const [rated, setRated] = useState<number | null>(null)
  const rate = useMutation({
    mutationFn: (rating: number) => api(`/ask/messages/${m.id}/feedback`, { method: 'POST', auth: true, json: { rating } }),
    onSuccess: (_d, rating) => setRated(rating),
  })
  return (
    <Card>
      <P>{m.content}</P>
      {m.citations.length > 0 && <H2>Sources used</H2>}
      {m.citations.map((c, i) => (
        <View key={i} style={{ gap: 4 }}>
          <P small>[E{i + 1}] {c.label}</P>
          {c.text_arabic ? <Arabic size={24}>{c.text_arabic}</Arabic> : null}
          {c.text ? <P>{c.text}</P> : null}
          <SourceCredit source={c.source} />
        </View>
      ))}
      {m.outcome === 'answered' && (
        <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
          <P small>Was this helpful?</P>
          <Button variant={rated === 1 ? 'primary' : 'secondary'} title="Yes" onPress={() => rate.mutate(1)} />
          <Button variant={rated === -1 ? 'primary' : 'secondary'} title="No" onPress={() => rate.mutate(-1)} />
        </View>
      )}
    </Card>
  )
}

export default function AskTab() {
  const { status } = useAuth()
  const [question, setQuestion] = useState('')
  const [conv, setConv] = useState<string | null>(null)
  const [turns, setTurns] = useState<{ q: string; m: ChatMessage }[]>([])
  const [disclaimer, setDisclaimer] = useState<string | null>(null)
  const ask = useMutation({
    mutationFn: (q: string) => api<AskResponse>('/ask', { method: 'POST', auth: true, json: { question: q, conversation_id: conv } }),
    onSuccess: (r, q) => { setConv(r.conversation_id); setDisclaimer(r.disclaimer); setTurns((t) => [...t, { q, m: r.message }]); setQuestion('') },
  })
  if (status !== 'authenticated') {
    return (
      <Screen>
        <P>Log in to ask questions. Answers come only from our approved sources and show exactly which ones.</P>
        <Link href="/login" asChild><Button title="Log in" onPress={() => undefined} /></Link>
      </Screen>
    )
  }
  return (
    <Screen>
      <P small>A learning aid, not a fatwa. For rulings or personal situations, ask a qualified scholar.</P>
      {turns.map((t, i) => (<View key={i} style={{ gap: 8 }}><P small>You asked: {t.q}</P><Answer m={t.m} /></View>))}
      {disclaimer ? <P small>{disclaimer}</P> : null}
      <Field label="Your question" multiline maxLength={1000} value={question} onChangeText={setQuestion} style={{ minHeight: 90, paddingTop: 12, textAlignVertical: 'top' }} />
      {ask.error ? <ErrorNote message={ask.error instanceof ApiError ? ask.error.message : 'Something went wrong.'} /> : null}
      <Button title={ask.isPending ? 'Looking through sources…' : 'Ask'} disabled={ask.isPending || question.trim().length < 3} onPress={() => ask.mutate(question.trim())} />
    </Screen>
  )
}
