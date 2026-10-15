import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Async, PageHeading } from '@/components/content/Async'
import { SourceCredit } from '@/components/content/SourceCredit'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { EmptyState } from '@/components/ui/EmptyState'
import { FormError } from '@/components/ui/FormMessage'
import { useAuth } from '@/features/auth/useAuth'
import { ApiError, api } from '@/lib/api'
import type { PathDetail, PathSummary, Quiz, QuizResult, QuizSummary } from '@/lib/types'

export function LearningPage() {
  const paths = useQuery({ queryKey: ['paths'], queryFn: () => api<PathSummary[]>('/learning/paths') })
  const quizzes = useQuery({ queryKey: ['quizzes'], queryFn: () => api<QuizSummary[]>('/quizzes') })
  return (
    <Container className="py-12">
      <PageHeading title="Learning">Guided paths and quizzes. Every quiz answer is explained with an approved source.</PageHeading>
      <h2 className="text-2xl">Paths</h2>
      <div className="mt-4">
        <Async query={paths}>
          {(items) => items.length === 0 ? (
            <EmptyState title="No learning paths yet">Paths are published after review. None have been approved so far.</EmptyState>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2">
              {items.map((p) => (
                <li key={p.slug}>
                  <Link to={`/learning/paths/${p.slug}`} className="block rounded-md border border-sand bg-white p-4 hover:border-emerald">
                    <span className="font-display text-lg text-emerald">{p.title}</span>
                    <span className="block text-xs text-charcoal/80">{p.difficulty} · {p.item_count} steps</span>
                    {p.description && <span className="mt-1 block text-sm">{p.description}</span>}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Async>
      </div>
      <h2 className="mt-12 text-2xl">Quizzes</h2>
      <div className="mt-4">
        <Async query={quizzes}>
          {(items) => items.length === 0 ? (
            <EmptyState title="No quizzes yet">Quizzes appear once they have been reviewed and every explanation is backed by an approved source.</EmptyState>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2">
              {items.map((q) => (
                <li key={q.id}>
                  <Link to={`/learning/quizzes/${q.id}`} className="block rounded-md border border-sand bg-white p-4 hover:border-emerald">
                    <span className="font-display text-lg text-emerald">{q.title}</span>
                    <span className="block text-xs text-charcoal/80">{q.difficulty} · {q.question_count} questions</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Async>
      </div>
    </Container>
  )
}

export function PathPage() {
  const { slug } = useParams()
  const { status } = useAuth()
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['path', slug, status], queryFn: () => api<PathDetail>(`/learning/paths/${slug}`, { auth: status === 'authenticated' }) })
  const save = useMutation({
    mutationFn: (position: number) => api<PathDetail>(`/learning/paths/${slug}/progress`, { method: 'PUT', auth: true, json: { last_item_position: position } }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['path', slug] }),
  })
  return (
    <Container className="max-w-3xl py-12">
      <Link to="/learning" className="text-sm text-emerald underline">Learning</Link>
      <Async query={q}>
        {(p) => (
          <>
            <h1 className="mt-4 text-3xl">{p.title}</h1>
            {p.description && <p className="mt-2">{p.description}</p>}
            {p.completed && <p className="mt-3 font-medium text-emerald">You have completed this path.</p>}
            <ol className="mt-8 space-y-3">
              {p.items.map((it) => (
                <li key={it.position}>
                  <Card className="flex flex-wrap items-center justify-between gap-3">
                    <span>{it.position}. {it.title}{it.position <= p.last_item_position && ' ✓'}</span>
                    <span className="flex gap-2">
                      {it.quiz_id && <Link className="text-sm text-emerald underline" to={`/learning/quizzes/${it.quiz_id}`}>Take quiz</Link>}
                      {status === 'authenticated' && it.position > p.last_item_position && (
                        <Button variant="secondary" disabled={save.isPending} onClick={() => save.mutate(it.position)}>Mark done</Button>
                      )}
                    </span>
                  </Card>
                </li>
              ))}
            </ol>
            {status === 'anonymous' && <p className="mt-6 text-sm"><Link className="underline" to="/login">Log in</Link> to save your progress.</p>}
          </>
        )}
      </Async>
    </Container>
  )
}

export function QuizPage() {
  const { id } = useParams()
  const { status } = useAuth()
  const q = useQuery({ queryKey: ['quiz', id], queryFn: () => api<Quiz>(`/quizzes/${id}`) })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const submit = useMutation({
    mutationFn: () => api<QuizResult>(`/quizzes/${id}/submit`, { method: 'POST', auth: true, json: { answers } }),
  })
  const result = submit.data
  return (
    <Container className="max-w-3xl py-12">
      <Link to="/learning" className="text-sm text-emerald underline">Learning</Link>
      <Async query={q}>
        {(quiz) => (
          <>
            <h1 className="mt-4 text-3xl">{quiz.title}</h1>
            {result && <p role="status" className="mt-4 text-xl font-semibold text-emerald">You scored {result.score} of {result.total}.</p>}
            <ol className="mt-6 space-y-5">
              {quiz.questions.map((qq, i) => {
                const r = result?.results.find((x) => x.question_id === qq.id)
                return (
                  <li key={qq.id}>
                    <Card>
                      <fieldset disabled={!!result}>
                        <legend className="font-medium">{i + 1}. {qq.prompt}</legend>
                        <div className="mt-3 space-y-2">
                          {qq.options.map((o) => (
                            <label key={o.id} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-md border border-sand px-3 py-2">
                              <input type="radio" name={`q${qq.id}`} checked={answers[qq.id] === o.id} onChange={() => setAnswers({ ...answers, [qq.id]: o.id })} />
                              <span>{o.text}{r && o.id === r.correct_option_id ? ' — correct answer' : ''}</span>
                            </label>
                          ))}
                        </div>
                      </fieldset>
                      {r && (
                        <div className="mt-3 text-sm">
                          <p className="font-medium">{r.is_correct ? 'Correct.' : 'Not quite.'}</p>
                          {r.explanation && <><p>{r.explanation.text}</p>{r.explanation.reference_text && <p>Reference: {r.explanation.reference_text}</p>}<SourceCredit source={r.explanation.source} /></>}
                        </div>
                      )}
                    </Card>
                  </li>
                )
              })}
            </ol>
            {submit.error && <div className="mt-4"><FormError title={submit.error instanceof ApiError ? submit.error.message : 'Something went wrong.'} /></div>}
            {!result && (
              status === 'authenticated' ? (
                <Button className="mt-6" disabled={submit.isPending} onClick={() => submit.mutate()}>Submit answers</Button>
              ) : (
                <p className="mt-6 text-sm"><Link className="underline" to="/login">Log in</Link> to submit and see your score.</p>
              )
            )}
          </>
        )}
      </Async>
    </Container>
  )
}
