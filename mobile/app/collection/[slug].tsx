import { useQuery } from '@tanstack/react-query'
import { Stack, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { View } from 'react-native'
import { api } from '@/lib/api'
import type { Hadith, Page } from '@/lib/types'
import { Arabic, Async, Button, Card, P, Screen, SourceCredit } from '@/ui/kit'

export function HadithCard({ h }: { h: Hadith }) {
  return (
    <Card>
      <P small>{h.collection_name} #{h.hadith_number}{h.book_name ? ` · ${h.book_name}` : ''}</P>
      {h.narrator ? <P small>Narrated by {h.narrator}</P> : null}
      {h.arabic_text ? <Arabic size={24}>{h.arabic_text}</Arabic> : null}
      {h.translation_text ? <P>{h.translation_text}</P> : null}
      <SourceCredit source={h.source} />
      {h.gradings.length > 0 && (
        <View>
          <P small>Gradings (each shown with who gave it):</P>
          {h.gradings.map((g) => <P key={g.grader} small>{g.grader}: {g.grade}{g.reference_note ? ` (${g.reference_note})` : ''}</P>)}
        </View>
      )}
    </Card>
  )
}

export default function CollectionScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>()
  const [offset, setOffset] = useState(0)
  const q = useQuery({ queryKey: ['collection', slug, offset], queryFn: () => api<Page<Hadith>>(`/hadith/collections/${slug}?limit=20&offset=${offset}`) })
  return (
    <Screen>
      <Stack.Screen options={{ title: q.data?.items[0]?.collection_name ?? 'Hadith' }} />
      <Async query={q}>
        {(p) => (
          <>
            {p.items.map((h) => <HadithCard key={h.id} h={h} />)}
            {p.total > p.limit && (
              <View style={{ flexDirection: 'row', gap: 8 }}>
                <Button variant="secondary" title="Previous" disabled={offset === 0} onPress={() => setOffset(Math.max(0, offset - p.limit))} />
                <Button variant="secondary" title="Next" disabled={offset + p.limit >= p.total} onPress={() => setOffset(offset + p.limit)} />
              </View>
            )}
          </>
        )}
      </Async>
    </Screen>
  )
}
