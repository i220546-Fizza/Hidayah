import { useQuery } from '@tanstack/react-query'
import { Text } from 'react-native'
import { api } from '@/lib/api'
import type { Surah } from '@/lib/types'
import { fonts, colors } from '@/theme/tokens'
import { Async, Empty, RowLink, Screen } from '@/ui/kit'

export default function Quran() {
  const q = useQuery({ queryKey: ['surahs'], queryFn: () => api<Surah[]>('/surahs') })
  return (
    <Screen>
      <Async query={q}>
        {(items) => items.length === 0 ? (
          <Empty title="The Quran text is not available yet">We are still confirming the licence for an Arabic text. Nothing is shown until a source is approved, because we never generate Quranic text.</Empty>
        ) : items.map((s) => (
          <RowLink key={s.number} href={`/surah/${s.number}`} title={`${s.number}. ${s.name_english}`} subtitle={`${s.verse_count} verses`}
            right={<Text style={{ fontFamily: fonts.arabic, fontSize: 24, color: colors.emerald }}>{s.name_arabic}</Text>} />
        ))}
      </Async>
    </Screen>
  )
}
