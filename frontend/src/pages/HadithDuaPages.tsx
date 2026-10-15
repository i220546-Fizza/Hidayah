import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Async, PageHeading } from '@/components/content/Async'
import { SourceCredit } from '@/components/content/SourceCredit'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Container } from '@/components/ui/Container'
import { EmptyState } from '@/components/ui/EmptyState'
import { api } from '@/lib/api'
import type { Collection, Dua, DuaCategory, Hadith, Page } from '@/lib/types'

export function HadithCard({ h, link = true }: { h: Hadith; link?: boolean }) {
  return (
    <Card>
      <p className="text-xs font-medium text-charcoal/80">
        {link ? <Link className="underline" to={`/hadith/${h.id}`}>{h.collection_name} #{h.hadith_number}</Link> : <>{h.collection_name} #{h.hadith_number}</>}
        {h.book_name ? ` · ${h.book_name}` : ''}
      </p>
      {h.narrator && <p className="mt-2 text-sm text-charcoal/80">Narrated by {h.narrator}</p>}
      {h.arabic_text && <p lang="ar" className="arabic mt-2 text-2xl text-emerald">{h.arabic_text}</p>}
      {h.translation_text && <p className="mt-3">{h.translation_text}</p>}
      <SourceCredit source={h.source} />
      {h.gradings.length > 0 && (
        <div className="mt-3 border-t border-sand pt-3">
          <p className="text-sm font-medium">Gradings</p>
          <ul className="mt-1 text-sm">
            {h.gradings.map((g) => (
              <li key={g.grader}>{g.grader}: {g.grade}{g.reference_note ? ` (${g.reference_note})` : ''}</li>
            ))}
          </ul>
          <p className="mt-1 text-xs text-charcoal/80">Scholars can differ in their gradings; each is shown with who gave it.</p>
        </div>
      )}
    </Card>
  )
}

export function HadithPage() {
  const q = useQuery({ queryKey: ['collections'], queryFn: () => api<Collection[]>('/hadith/collections') })
  return (
    <Container className="py-12">
      <PageHeading title="Hadith">Browse collections whose licence we have verified. Each narration shows its collection and number.</PageHeading>
      <Async query={q}>
        {(items) =>
          items.length === 0 ? (
            <EmptyState title="No hadith collections are available yet">
              We are requesting permission from the rights holders of recognised collections. Nothing appears here until a source is approved.
            </EmptyState>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2">
              {items.map((c) => (
                <li key={c.slug}>
                  <Link to={`/hadith/collections/${c.slug}`} className="block rounded-md border border-sand bg-white p-4 hover:border-emerald">
                    <span className="font-display text-lg text-emerald">{c.name_english}</span>
                    <span className="block text-xs text-charcoal/80">{c.record_count} narrations</span>
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

export function CollectionPage() {
  const { slug } = useParams()
  const [params, setParams] = useSearchParams()
  const offset = Number(params.get('offset') ?? 0) || 0
  const q = useQuery({ queryKey: ['collection', slug, offset], queryFn: () => api<Page<Hadith>>(`/hadith/collections/${slug}?limit=20&offset=${offset}`) })
  return (
    <Container className="py-12">
      <Link to="/hadith" className="text-sm text-emerald underline">All collections</Link>
      <Async query={q}>
        {(p) => (
          <>
            <h1 className="mt-4 text-3xl">{p.items[0]?.collection_name ?? 'Collection'}</h1>
            <ul className="mt-8 space-y-4">{p.items.map((h) => <li key={h.id}><HadithCard h={h} /></li>)}</ul>
            {p.total > p.limit && (
              <nav className="mt-8 flex gap-3" aria-label="Pages of narrations">
                <Button variant="secondary" disabled={offset === 0} onClick={() => setParams({ offset: String(Math.max(0, offset - p.limit)) })}>Previous</Button>
                <Button variant="secondary" disabled={offset + p.limit >= p.total} onClick={() => setParams({ offset: String(offset + p.limit) })}>Next</Button>
              </nav>
            )}
          </>
        )}
      </Async>
    </Container>
  )
}

export function HadithDetailPage() {
  const { id } = useParams()
  const q = useQuery({ queryKey: ['hadith', id], queryFn: () => api<Hadith>(`/hadith/${id}`) })
  return (
    <Container className="max-w-3xl py-12">
      <Link to="/hadith" className="text-sm text-emerald underline">Hadith</Link>
      <div className="mt-4"><Async query={q}>{(h) => <HadithCard h={h} link={false} />}</Async></div>
    </Container>
  )
}

export function DuasPage() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category')
  const cats = useQuery({ queryKey: ['dua-cats'], queryFn: () => api<DuaCategory[]>('/duas/categories') })
  const list = useQuery({ queryKey: ['duas', category], queryFn: () => api<Dua[]>(`/duas${category ? `?category=${encodeURIComponent(category)}` : ''}`) })
  return (
    <Container className="py-12">
      <PageHeading title="Duas">Supplications with their Arabic, translation and the reference each comes from.</PageHeading>
      <Async query={cats}>
        {(c) =>
          c.length > 0 && (
            <div className="mb-8 flex flex-wrap gap-2" role="group" aria-label="Categories">
              <Button variant={category ? 'secondary' : 'primary'} onClick={() => setParams({})}>All</Button>
              {c.map((x) => (
                <Button key={x.slug} variant={category === x.slug ? 'primary' : 'secondary'} onClick={() => setParams({ category: x.slug })}>
                  {x.name_english} ({x.dua_count})
                </Button>
              ))}
            </div>
          )
        }
      </Async>
      <Async query={list}>
        {(items) =>
          items.length === 0 ? (
            <EmptyState title="No duas are available yet">
              Duas appear once supplications with checked references and an approved source have been added. We do not show duas without a reference.
            </EmptyState>
          ) : (
            <ul className="space-y-4">
              {items.map((d) => (
                <li key={d.id} id={String(d.id)}>
                  <Card>
                    <h2 className="font-display text-xl text-emerald">{d.title}</h2>
                    <p lang="ar" className="arabic mt-3 text-2xl text-emerald">{d.arabic_text}</p>
                    {d.transliteration && <p className="mt-2 italic">{d.transliteration}</p>}
                    {d.translation_text && <p className="mt-2">{d.translation_text}</p>}
                    {d.reference_text && <p className="mt-3 text-sm font-medium">Reference: {d.reference_text}</p>}
                    <SourceCredit source={d.source} />
                  </Card>
                </li>
              ))}
            </ul>
          )
        }
      </Async>
    </Container>
  )
}
