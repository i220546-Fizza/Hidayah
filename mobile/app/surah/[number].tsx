import { useQuery } from '@tanstack/react-query'
import { Stack, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { View } from 'react-native'
import { api } from '@/lib/api'
import type { SurahDetail, Tafsir } from '@/lib/types'
import { Arabic, Async, Button, Card, Empty, P, Screen, SourceCredit } from '@/ui/kit'

function TafsirPanel({ surah, verse }: { surah: number; verse: number }) {
  const q = useQuery({ queryKey: ['tafsir', surah, verse], queryFn: () => api<Tafsir[]>(`/verses/${surah}/${verse}/tafsir`) })
  return (
    <Async query={q}>
      {(items) => items.length === 0 ? <P small>No approved tafsir is available for this verse yet.</P> : (
        <View style={{ gap: 8 }}>{items.map((t, i) => <View key={i}><P>{t.text}</P><SourceCredit source={t.source} /></View>)}</View>
      )}
    </Async>
  )
}

export default function SurahScreen() {
  const { number } = useLocalSearchParams<{ number: string }>()
  const [offset, setOffset] = useState(0)
  const [size, setSize] = useState(28)
  const [open, setOpen] = useState<number | null>(null)
  const q = useQuery({ queryKey: ['surah', number, offset], queryFn: () => api<SurahDetail>(`/surahs/${number}?language=en&limit=50&offset=${offset}`) })
  return (
    <Screen>
      <Stack.Screen options={{ title: q.data ? q.data.surah.name_english : 'Surah' }} />
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <Button variant="secondary" title="A−" disabled={size <= 22} onPress={() => setSize(size - 4)} />
        <Button variant="secondary" title="A+" disabled={size >= 44} onPress={() => setSize(size + 4)} />
      </View>
      <Async query={q}>
        {(d) => d.verses.length === 0 ? (
          <Empty title="No approved text for this surah yet">Verses appear once an approved source has been imported.</Empty>
        ) : (
          <>
            {d.verses.map((v) => (
              <Card key={v.verse_number}>
                <P small>{v.surah_number}:{v.verse_number}</P>
                <Arabic size={size}>{v.text_arabic}</Arabic>
                <SourceCredit source={v.source} label="Arabic text" />
                {v.translations.map((t, i) => <View key={i}><P>{t.text}</P><SourceCredit source={t.source} label="Translation" /></View>)}
                <Button variant="secondary" title={open === v.verse_number ? 'Hide tafsir' : 'Show tafsir'} onPress={() => setOpen(open === v.verse_number ? null : v.verse_number)} />
                {open === v.verse_number && <TafsirPanel surah={v.surah_number} verse={v.verse_number} />}
              </Card>
            ))}
            {d.total > d.limit && (
              <View style={{ flexDirection: 'row', gap: 8 }}>
                <Button variant="secondary" title="Previous" disabled={offset === 0} onPress={() => setOffset(Math.max(0, offset - d.limit))} />
                <Button variant="secondary" title="Next" disabled={offset + d.limit >= d.total} onPress={() => setOffset(offset + d.limit)} />
              </View>
            )}
          </>
        )}
      </Async>
    </Screen>
  )
}
