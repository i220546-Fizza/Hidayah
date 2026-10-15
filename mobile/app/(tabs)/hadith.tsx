import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Collection } from '@/lib/types'
import { Async, Empty, RowLink, Screen } from '@/ui/kit'

export default function HadithTab() {
  const q = useQuery({ queryKey: ['collections'], queryFn: () => api<Collection[]>('/hadith/collections') })
  return (
    <Screen>
      <Async query={q}>
        {(items) => items.length === 0 ? (
          <Empty title="No hadith collections are available yet">We are requesting permission from the rights holders of recognised collections. Nothing appears until a source is approved.</Empty>
        ) : items.map((c) => <RowLink key={c.slug} href={`/collection/${c.slug}`} title={c.name_english} subtitle={`${c.record_count} narrations`} />)}
      </Async>
    </Screen>
  )
}
