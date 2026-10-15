import { useMutation, useQuery } from '@tanstack/react-query'
import { Stack, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { Pressable, Text } from 'react-native'
import { useAuth } from '@/auth/AuthContext'
import { ApiError, api } from '@/lib/api'
import type { Quiz, QuizResult } from '@/lib/types'
import { colors, fonts, minTouchTarget, radius } from '@/theme/tokens'
import { Async, Button, Card, ErrorNote, H1, H2, P, Screen, SourceCredit } from '@/ui/kit'

export default function QuizScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { status } = useAuth()
  const q = useQuery({ queryKey: ['quiz', id], queryFn: () => api<Quiz>(`/quizzes/${id}`) })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const submit = useMutation({ mutationFn: () => api<QuizResult>(`/quizzes/${id}/submit`, { method: 'POST', auth: true, json: { answers } }) })
  const result = submit.data
  return (
    <Screen>
      <Stack.Screen options={{ title: q.data?.title ?? 'Quiz' }} />
      <Async query={q}>
        {(quiz) => (
          <>
            <H1>{quiz.title}</H1>
            {result ? <H2>You scored {result.score} of {result.total}</H2> : null}
            {quiz.questions.map((qq, i) => {
              const r = result?.results.find((x) => x.question_id === qq.id)
              return (
                <Card key={qq.id}>
                  <P>{i + 1}. {qq.prompt}</P>
                  {qq.options.map((o) => {
                    const chosen = answers[qq.id] === o.id
                    return (
                      <Pressable key={o.id} accessibilityRole="radio" accessibilityState={{ selected: chosen, disabled: !!result }} disabled={!!result}
                        onPress={() => setAnswers({ ...answers, [qq.id]: o.id })}
                        style={{ minHeight: minTouchTarget, justifyContent: 'center', borderWidth: 1, borderRadius: radius.md, paddingHorizontal: 12, borderColor: chosen ? colors.emerald : colors.sand, backgroundColor: chosen ? colors.sand : colors.white }}>
                        <Text style={{ fontFamily: fonts.sans, color: colors.charcoal }}>{o.text}{r && o.id === r.correct_option_id ? ' — correct answer' : ''}</Text>
                      </Pressable>
                    )
                  })}
                  {r ? (<><P>{r.is_correct ? 'Correct.' : 'Not quite.'}</P>{r.explanation ? <><P small>{r.explanation.text}</P>{r.explanation.reference_text ? <P small>Reference: {r.explanation.reference_text}</P> : null}<SourceCredit source={r.explanation.source} /></> : null}</>) : null}
                </Card>
              )
            })}
            {submit.error ? <ErrorNote message={submit.error instanceof ApiError ? submit.error.message : 'Something went wrong.'} /> : null}
            {!result && (status === 'authenticated'
              ? <Button title="Submit answers" disabled={submit.isPending} onPress={() => submit.mutate()} />
              : <P small>Log in to submit and see your score.</P>)}
          </>
        )}
      </Async>
    </Screen>
  )
}
