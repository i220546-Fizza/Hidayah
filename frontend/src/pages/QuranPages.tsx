import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Async, PageHeading } from '@/components/content/Async'
import { SourceCredit } from '@/components/content/SourceCredit'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { EmptyState } from '@/components/ui/EmptyState'
import { api } from '@/lib/api'
import type { Surah, SurahDetail, Tafsir } from '@/lib/types'
import { useArabicSize } from '@/lib/useReadingSize'
import { useState } from 'react'

export function QuranPage() {
  const q = useQuery({ queryKey: ['surahs'], queryFn: () => api<Surah[]>('/surahs') })
  return (
    <Container className="py-12">
      <PageHeading title="Quran">Read each surah in Arabic with approved translations. Text appears only from sources whose licence we have verified.</PageHeading>
      <Async query={q}>
        {(surahs) =>
          surahs.length === 0 ? (
            <EmptyState title="The Quran text is not available yet">
              We are still confirming the licence for an Arabic text. Nothing is shown here until a source is approved, because we never generate or guess Quranic text.
            </EmptyState>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {surahs.map((s) => (
                <li key={s.number}>
                  <Link to={`/quran/${s.number}`} className="flex items-center justify-between rounded-md border border-sand bg-white p-4 hover:border-emerald">
                    <span>
                      <span className="text-sm text-charcoal/80">{s.number}.</span>{' '}
                      <span className="font-display text-lg text-emerald">{s.name_english}</span>
                      <span className="block text-xs text-charcoal/80">{s.verse_count} verses</span>
                    </span>
                    <span lang="ar" className="arabic text-2xl text-emerald">{s.name_arabic}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )
        }
      </Async>
    </Container>
  )
}

function TafsirPanel({ surah, verse }: { surah: number; verse: number }) {
  const q = useQuery({ queryKey: ['tafsir', surah, verse], queryFn: () => api<Tafsir[]>(`/verses/${surah}/${verse}/tafsir`) })
  return (
    <div className="mt-3 rounded-md bg-ivory p-4">
      <Async query={q}>
        {(items) =>
          items.length === 0 ? (
            <p className="text-sm text-charcoal/80">No approved tafsir is available for this verse yet.</p>
          ) : (
            items.map((t, i) => (
              <div key={i} className="mb-3 last:mb-0">
                <p className="whitespace-pre-line text-sm">{t.text}</p>
                <SourceCredit source={t.source} />
              </div>
            ))
          )
        }
      </Async>
    </div>
  )
}

export function SurahPage() {
  const { number } = useParams()
  const [params, setParams] = useSearchParams()
  const offset = Number(params.get('offset') ?? 0) || 0
  const size = useArabicSize()
  const [open, setOpen] = useState<number | null>(null)
  const q = useQuery({
    queryKey: ['surah', number, offset],
    queryFn: () => api<SurahDetail>(`/surahs/${number}?language=en&limit=50&offset=${offset}`),
  })
  return (
    <Container className="py-12">
      <Link to="/quran" className="text-sm text-emerald underline">All surahs</Link>
      <Async query={q}>
        {(d) => (
          <>
            <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl sm:text-4xl">{d.surah.number}. {d.surah.name_english}</h1>
                <p lang="ar" className="arabic mt-2 text-3xl text-emerald">{d.surah.name_arabic}</p>
              </div>
              <div className="flex items-center gap-2" role="group" aria-label="Arabic text size">
                <Button variant="secondary" disabled={!size.canSmaller} onClick={size.smaller} aria-label="Smaller Arabic text">A−</Button>
                <Button variant="secondary" disabled={!size.canBigger} onClick={size.bigger} aria-label="Larger Arabic text">A+</Button>
              </div>
            </div>
            {d.verses.length === 0 ? (
              <div className="mt-8">
                <EmptyState title="No approved text for this surah yet">Verses appear here once an approved source has been imported.</EmptyState>
              </div>
            ) : (
              <ol className="mt-8 space-y-4">
                {d.verses.map((v) => (
                  <li key={v.verse_number} id={`v${v.verse_number}`}>
                    <Card>
                      <p className="text-xs font-medium text-charcoal/80">{v.surah_number}:{v.verse_number}</p>
                      <p lang="ar" className={`arabic mt-2 ${size.className} text-emerald`}>{v.text_arabic}</p>
                      <SourceCredit source={v.source} label="Arabic text" />
                      {v.translations.map((t, i) => (
                        <div key={i} className="mt-4 border-t border-sand pt-3">
                          <p>{t.text}</p>
                          <SourceCredit source={t.source} label="Translation" />
                        </div>
                      ))}
                      <Button variant="quiet" className="mt-3" aria-expanded={open === v.verse_number}
                        onClick={() => setOpen(open === v.verse_number ? null : v.verse_number)}>
                        {open === v.verse_number ? 'Hide tafsir' : 'Show tafsir'}
                      </Button>
                      {open === v.verse_number && <TafsirPanel surah={v.surah_number} verse={v.verse_number} />}
                    </Card>
                  </li>
                ))}
              </ol>
            )}
            {d.total > d.limit && (
              <nav className="mt-8 flex gap-3" aria-label="Pages of verses">
                <Button variant="secondary" disabled={offset === 0} onClick={() => setParams({ offset: String(Math.max(0, offset - d.limit)) })}>Previous</Button>
                <Button variant="secondary" disabled={offset + d.limit >= d.total} onClick={() => setParams({ offset: String(offset + d.limit) })}>Next</Button>
              </nav>
            )}
          </>
        )}
      </Async>
    </Container>
  )
}
