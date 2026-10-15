import { useQuery } from '@tanstack/react-query'
import { Stack } from 'expo-router'
import { api } from '@/lib/api'
import type { Source } from '@/lib/types'
import { Async, Card, Empty, H2, P, Screen } from '@/ui/kit'

export default function SourcesScreen() {
  const q = useQuery({ queryKey: ['sources'], queryFn: () => api<Source[]>('/sources') })
  return (
    <Screen>
      <Stack.Screen options={{ title: 'Sources and credits' }} />
      <P>Only sources that passed our licence and content review appear here.</P>
      <Async query={q}>
        {(items) => items.length === 0 ? (
          <Empty title="No sources are approved yet">We are verifying licences before importing anything. This list fills in as each source is approved.</Empty>
        ) : items.map((s) => (
          <Card key={s.slug}>
            <H2>{s.title}</H2>
            <P small>{[s.edition, s.author_or_publisher, s.translator && `Translator: ${s.translator}`].filter(Boolean).join(' · ')}</P>
            {s.attribution_text ? <P small>{s.attribution_text}</P> : null}
            <P small>{s.rights_holder ? `Rights holder: ${s.rights_holder}. ` : ''}{s.license_name ?? ''}</P>
          </Card>
        ))}
      </Async>
    </Screen>
  )
}
