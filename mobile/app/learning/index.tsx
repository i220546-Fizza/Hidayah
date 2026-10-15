import { useQuery } from '@tanstack/react-query'
import { Stack } from 'expo-router'
import { api } from '@/lib/api'
import type { PathSummary, QuizSummary } from '@/lib/types'
import { Async, Empty, H2, RowLink, Screen } from '@/ui/kit'

export default function Learning() {
  const paths = useQuery({ queryKey: ['paths'], queryFn: () => api<PathSummary[]>('/learning/paths') })
  const quizzes = useQuery({ queryKey: ['quizzes'], queryFn: () => api<QuizSummary[]>('/quizzes') })
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Learning' }} />
      <H2>Paths</H2>
      <Async query={paths}>{(items) => items.length === 0 ? <Empty title="No learning paths yet">Paths are published after review.</Empty> :
        items.map((p) => <RowLink key={p.slug} href={`/learning/path/${p.slug}`} title={p.title} subtitle={`${p.difficulty} · ${p.item_count} steps`} />)}</Async>
      <H2>Quizzes</H2>
      <Async query={quizzes}>{(items) => items.length === 0 ? <Empty title="No quizzes yet">Quizzes appear once reviewed and every explanation is backed by an approved source.</Empty> :
        items.map((q) => <RowLink key={q.id} href={`/learning/quiz/${q.id}`} title={q.title} subtitle={`${q.difficulty} · ${q.question_count} questions`} />)}</Async>
    </Screen>
  )
}
