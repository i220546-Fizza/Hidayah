import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Daily } from '@/lib/types'
import { Arabic, Async, Card, Empty, H1, H2, P, RowLink, Screen, SourceCredit } from '@/ui/kit'

export default function Home() {
  const daily = useQuery({ queryKey: ['daily'], queryFn: () => api<Daily>('/daily') })
  return (
    <Screen>
      <H1>Hidayah</H1>
      <P>Read, search and learn from Islamic sources, always with where each text came from.</P>
      <H2>Today’s verse</H2>
      <Async query={daily}>
        {(d) =>
          d.verse ? (
            <Card>
              <P small>{d.verse.surah_number}:{d.verse.verse_number}</P>
              <Arabic>{d.verse.text_arabic}</Arabic>
              <SourceCredit source={d.verse.source} label="Arabic text" />
              {d.verse.translations.slice(0, 1).map((t, i) => (<P key={i}>{t.text}</P>))}
              {d.verse.translations.slice(0, 1).map((t, i) => (<SourceCredit key={i} source={t.source} label="Translation" />))}
            </Card>
          ) : (
            <Empty title="Not available yet">The daily verse appears once approved Quran text is available. We never show text we cannot trace to a licensed source.</Empty>
          )
        }
      </Async>
      <RowLink href="/learning" title="Learning" subtitle="Paths and quizzes" />
      <RowLink href="/search" title="Search" subtitle="Find words in approved sources" />
    </Screen>
  )
}
