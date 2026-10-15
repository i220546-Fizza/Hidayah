import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Async, PageHeading } from '@/components/content/Async'
import { SourceCredit } from '@/components/content/SourceCredit'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { TextField } from '@/components/ui/TextField'
import { api } from '@/lib/api'
import type { SearchHit } from '@/lib/types'

const TYPE_LABEL: Record<string, string> = { verse_translation: 'Quran', hadith: 'Hadith', dua: 'Dua', tafsir: 'Tafsir' }

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const term = params.get('q') ?? ''
  const [text, setText] = useState(term)
  const q = useQuery({
    queryKey: ['search', term],
    enabled: term.trim().length >= 2,
    queryFn: () => api<{ hits: SearchHit[]; note: string | null }>(`/search?q=${encodeURIComponent(term)}`),
  })
  return (
    <Container className="py-12">
      <PageHeading title="Search">Searches the text of approved sources by words. For a question in plain language, use Ask.</PageHeading>
      <form className="flex max-w-xl items-end gap-3" onSubmit={(e) => { e.preventDefault(); setParams(text.trim() ? { q: text.trim() } : {}) }}>
        <div className="flex-1"><TextField label="Search words" value={text} onChange={(e) => setText(e.target.value)} /></div>
        <Button type="submit">Search</Button>
      </form>
      {term.trim().length >= 2 && (
        <div className="mt-8">
          <Async query={q}>
            {(r) =>
              r.hits.length === 0 ? (
                <p>{r.note ?? 'No results.'}</p>
              ) : (
                <ul className="space-y-3">
                  {r.hits.map((h, i) => (
                    <li key={i}>
                      <Card>
                        <p className="text-xs font-medium text-charcoal/80">{TYPE_LABEL[h.type] ?? h.type}</p>
                        <Link to={h.link} className="font-display text-lg text-emerald underline">{h.title}</Link>
                        <p className="mt-1 text-sm">{h.snippet}</p>
                        <SourceCredit source={h.source} />
                      </Card>
                    </li>
                  ))}
                </ul>
              )
            }
          </Async>
        </div>
      )}
    </Container>
  )
}
