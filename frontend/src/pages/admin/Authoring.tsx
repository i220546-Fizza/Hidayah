import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { ApiError, api } from '@/lib/api'
import type { AdminSource, Page } from '@/lib/types'

const errText = (e: unknown) => (e instanceof ApiError ? [e.message, ...e.details].join(' ') : e ? 'Something went wrong.' : null)
const select = 'mt-1 block min-h-11 w-full rounded-md border border-sage bg-white px-3 text-sm'
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced']

type Q = { prompt: string; options: string[]; correct: number; explanation: string; reference: string; sourceId: string }
const blankQ = (): Q => ({ prompt: '', options: ['', ''], correct: 0, explanation: '', reference: '', sourceId: '' })

export function QuizBuilder() {
  const qc = useQueryClient()
  const sources = useQuery({
    queryKey: ['approved-sources'],
    queryFn: () => api<Page<AdminSource>>('/admin/sources?status=approved&limit=100', { auth: true }),
  })
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('beginner')
  const [qs, setQs] = useState<Q[]>([blankQ()])
  const edit = (i: number, patch: Partial<Q>) => setQs(qs.map((q, j) => (j === i ? { ...q, ...patch } : q)))
  const create = useMutation({
    mutationFn: () =>
      api('/admin/quizzes', {
        method: 'POST', auth: true,
        json: {
          title, topic: topic || null, difficulty,
          questions: qs.map((q) => ({
            prompt: q.prompt,
            options: q.options.map((text, i) => ({ text, is_correct: i === q.correct })),
            explanation: q.sourceId && q.explanation ? { text: q.explanation, source_id: Number(q.sourceId), reference_text: q.reference || null } : null,
          })),
        },
      }),
    onSuccess: () => {
      setTitle(''); setTopic(''); setQs([blankQ()])
      void qc.invalidateQueries({ queryKey: ['/admin/quizzes'] })
    },
  })
  const ready = title.trim().length >= 3 && qs.every((q) => q.prompt.trim().length >= 3 && q.options.length >= 2 && q.options.every((o) => o.trim()))
  return (
    <Card className="space-y-4">
      <h3 className="font-display text-xl">New quiz</h3>
      <p className="text-sm">A quiz starts as a draft. It can only be approved when every question has an explanation backed by an approved source.</p>
      <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); create.mutate() }}>
        <div className="grid gap-3 sm:grid-cols-3">
          <TextField label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <TextField label="Topic (optional)" value={topic} onChange={(e) => setTopic(e.target.value)} />
          <label className="text-sm font-medium">Difficulty
            <select className={select} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>{DIFFICULTIES.map((d) => <option key={d}>{d}</option>)}</select>
          </label>
        </div>
        {qs.map((q, i) => (
          <fieldset key={i} className="space-y-3 rounded-md border border-sand p-4">
            <legend className="px-1 text-sm font-medium">Question {i + 1}</legend>
            <TextField label="Question text" value={q.prompt} onChange={(e) => edit(i, { prompt: e.target.value })} />
            {q.options.map((o, k) => (
              <div key={k} className="flex items-end gap-2">
                <div className="flex-1"><TextField label={`Option ${k + 1}`} value={o} onChange={(e) => edit(i, { options: q.options.map((x, m) => (m === k ? e.target.value : x)) })} /></div>
                <label className="flex min-h-11 items-center gap-2 text-sm">
                  <input type="radio" name={`correct-${i}`} checked={q.correct === k} onChange={() => edit(i, { correct: k })} /> Correct
                </label>
              </div>
            ))}
            <div className="flex gap-2">
              {q.options.length < 6 && <Button type="button" variant="secondary" onClick={() => edit(i, { options: [...q.options, ''] })}>Add option</Button>}
              {qs.length > 1 && <Button type="button" variant="quiet" onClick={() => setQs(qs.filter((_, j) => j !== i))}>Remove question</Button>}
            </div>
            <TextField label="Explanation" value={q.explanation} onChange={(e) => edit(i, { explanation: e.target.value })} />
            <TextField label="Reference (for example a verse or hadith number)" value={q.reference} onChange={(e) => edit(i, { reference: e.target.value })} />
            <label className="block text-sm font-medium">Supporting approved source
              <select className={select} value={q.sourceId} onChange={(e) => edit(i, { sourceId: e.target.value })}>
                <option value="">— none yet (quiz cannot be approved) —</option>
                {sources.data?.items.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
              </select>
            </label>
          </fieldset>
        ))}
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => setQs([...qs, blankQ()])}>Add question</Button>
          <Button type="submit" disabled={!ready || create.isPending}>Save quiz as draft</Button>
        </div>
        {create.error && <FormError title={errText(create.error)!} />}
        {create.isSuccess && <p role="status" className="text-sm text-emerald">Quiz saved as a draft.</p>}
      </form>
    </Card>
  )
}

type Item = { title: string; quizId: string }

export function PathBuilder() {
  const qc = useQueryClient()
  const quizzes = useQuery({ queryKey: ['/admin/quizzes'], queryFn: () => api<{ id: number; title: string }[]>('/admin/quizzes', { auth: true }) })
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [difficulty, setDifficulty] = useState('beginner')
  const [items, setItems] = useState<Item[]>([{ title: '', quizId: '' }])
  const create = useMutation({
    mutationFn: () =>
      api('/admin/paths', {
        method: 'POST', auth: true,
        json: { slug, title, description: description || null, difficulty, items: items.map((i) => ({ title: i.title, quiz_id: i.quizId ? Number(i.quizId) : null })) },
      }),
    onSuccess: () => {
      setSlug(''); setTitle(''); setDescription(''); setItems([{ title: '', quizId: '' }])
      void qc.invalidateQueries({ queryKey: ['/admin/paths'] })
    },
  })
  const ready = /^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug) && title.trim().length >= 3 && items.every((i) => i.title.trim().length >= 2)
  return (
    <Card className="space-y-4">
      <h3 className="font-display text-xl">New learning path</h3>
      <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); create.mutate() }}>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField label="Slug (lowercase-with-dashes)" value={slug} onChange={(e) => setSlug(e.target.value)} />
          <TextField label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <TextField label="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} />
          <label className="text-sm font-medium">Difficulty
            <select className={select} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>{DIFFICULTIES.map((d) => <option key={d}>{d}</option>)}</select>
          </label>
        </div>
        {items.map((it, i) => (
          <div key={i} className="flex flex-wrap items-end gap-2">
            <div className="min-w-48 flex-1"><TextField label={`Step ${i + 1}`} value={it.title} onChange={(e) => setItems(items.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))} /></div>
            <label className="text-sm font-medium">Quiz (optional)
              <select className={select} value={it.quizId} onChange={(e) => setItems(items.map((x, j) => (j === i ? { ...x, quizId: e.target.value } : x)))}>
                <option value="">none</option>
                {quizzes.data?.map((q) => <option key={q.id} value={q.id}>{q.title}</option>)}
              </select>
            </label>
            {items.length > 1 && <Button type="button" variant="quiet" onClick={() => setItems(items.filter((_, j) => j !== i))}>Remove</Button>}
          </div>
        ))}
        <div className="flex gap-2">
          <Button type="button" variant="secondary" onClick={() => setItems([...items, { title: '', quizId: '' }])}>Add step</Button>
          <Button type="submit" disabled={!ready || create.isPending}>Save path as draft</Button>
        </div>
        {create.error && <FormError title={errText(create.error)!} />}
        {create.isSuccess && <p role="status" className="text-sm text-emerald">Path saved as a draft.</p>}
      </form>
    </Card>
  )
}
