import { useMutation } from '@tanstack/react-query'
import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { SourceCredit } from '@/components/content/SourceCredit'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { FormError } from '@/components/ui/FormMessage'
import { useAuth } from '@/features/auth/useAuth'
import { ApiError, api } from '@/lib/api'
import type { AskResponse, ChatMessage } from '@/lib/types'

type Turn = { question: string; answer: ChatMessage }

function Answer({ m }: { m: ChatMessage }) {
  const [rated, setRated] = useState<number | null>(null)
  const rate = useMutation({
    mutationFn: (rating: number) => api(`/ask/messages/${m.id}/feedback`, { method: 'POST', auth: true, json: { rating } }),
    onSuccess: (_d, rating) => setRated(rating),
  })
  return (
    <Card className={m.outcome === 'answered' ? '' : 'bg-ivory'}>
      <p>{m.content}</p>
      {m.outcome === 'insufficient_evidence' && <p className="mt-2 text-xs text-charcoal/80">No answer was generated because nothing in the approved sources matched.</p>}
      {m.citations.length > 0 && (
        <div className="mt-4 border-t border-sand pt-3">
          <h3 className="font-display text-base text-emerald">Sources used</h3>
          <ol className="mt-2 space-y-3">
            {m.citations.map((c, i) => (
              <li key={i} className="text-sm">
                <span className="font-medium">[E{i + 1}] {c.link ? <Link className="underline" to={c.link}>{c.label}</Link> : c.label}</span>
                {c.text_arabic && <p lang="ar" className="arabic mt-1 text-xl text-emerald">{c.text_arabic}</p>}
                {c.text && <p className="mt-1">{c.text}</p>}
                <SourceCredit source={c.source} />
              </li>
            ))}
          </ol>
        </div>
      )}
      {m.outcome === 'answered' && (
        <div className="mt-4 flex items-center gap-2 text-sm">
          <span>Was this helpful?</span>
          <Button variant={rated === 1 ? 'primary' : 'secondary'} aria-label="Helpful" aria-pressed={rated === 1} onClick={() => rate.mutate(1)}><ThumbsUp size={16} /></Button>
          <Button variant={rated === -1 ? 'primary' : 'secondary'} aria-label="Not helpful" aria-pressed={rated === -1} onClick={() => rate.mutate(-1)}><ThumbsDown size={16} /></Button>
        </div>
      )}
    </Card>
  )
}

export function AskPage() {
  const { status } = useAuth()
  const [params] = useSearchParams()
  const [question, setQuestion] = useState(params.get('q') ?? '')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [turns, setTurns] = useState<Turn[]>([])
  const [disclaimer, setDisclaimer] = useState<string | null>(null)
  const ask = useMutation({
    mutationFn: (q: string) => api<AskResponse>('/ask', { method: 'POST', auth: true, json: { question: q, conversation_id: conversationId } }),
    onSuccess: (r, q) => {
      setConversationId(r.conversation_id)
      setDisclaimer(r.disclaimer)
      setTurns((t) => [...t, { question: q, answer: r.message }])
      setQuestion('')
    },
  })
  const error = ask.error instanceof ApiError ? ask.error.message : ask.error ? 'Something went wrong.' : null

  return (
    <Container className="max-w-3xl py-12">
      <h1 className="text-3xl sm:text-4xl">Ask a question</h1>
      <p className="mt-3 text-charcoal/85">Answers are written only from our approved sources and show exactly which ones. This is a learning aid, not a fatwa.</p>
      {status === 'anonymous' ? (
        <Card className="mt-8">
          <p>Please <Link className="text-emerald underline" to="/login" state={{ from: '/ask' }}>log in</Link> or <Link className="text-emerald underline" to="/register">create an account</Link> to ask questions.</p>
        </Card>
      ) : (
        <>
          <ul className="mt-8 space-y-6">
            {turns.map((t, i) => (
              <li key={i}>
                <p className="mb-2 text-sm font-medium text-charcoal/85">You asked: {t.question}</p>
                <Answer m={t.answer} />
              </li>
            ))}
          </ul>
          {disclaimer && <p className="mt-4 text-xs text-charcoal/80">{disclaimer}</p>}
          <form className="mt-8 space-y-3" onSubmit={(e) => { e.preventDefault(); if (question.trim().length >= 3) ask.mutate(question.trim()) }}>
            <label htmlFor="q" className="block text-sm font-medium">Your question</label>
            <textarea id="q" rows={3} maxLength={1000} value={question} onChange={(e) => setQuestion(e.target.value)}
              className="w-full rounded-md border border-sage bg-white p-3 text-sm focus:border-emerald" />
            {error && <FormError title={error} />}
            <Button type="submit" disabled={ask.isPending || question.trim().length < 3}>{ask.isPending ? 'Looking through sources…' : 'Ask'}</Button>
          </form>
        </>
      )}
    </Container>
  )
}
