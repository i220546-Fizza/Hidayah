import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Dua } from '@/lib/types'
import { Arabic, Async, Card, Empty, H2, P, Screen, SourceCredit } from '@/ui/kit'

export default function DuasTab() {
  const q = useQuery({ queryKey: ['duas'], queryFn: () => api<Dua[]>('/duas') })
  return (
    <Screen>
      <Async query={q}>
        {(items) => items.length === 0 ? (
          <Empty title="No duas are available yet">Duas appear once supplications with checked references and an approved source have been added. We do not show duas without a reference.</Empty>
        ) : items.map((d) => (
          <Card key={d.id}>
            <H2>{d.title}</H2>
            <Arabic size={26}>{d.arabic_text}</Arabic>
            {d.transliteration ? <P>{d.transliteration}</P> : null}
            {d.translation_text ? <P>{d.translation_text}</P> : null}
            {d.reference_text ? <P small>Reference: {d.reference_text}</P> : null}
            <SourceCredit source={d.source} />
          </Card>
        ))}
      </Async>
    </Screen>
  )
}
