import { Stack } from 'expo-router'
import { H2, P, Screen } from '@/ui/kit'

export default function About() {
  return (
    <Screen>
      <Stack.Screen options={{ title: 'About' }} />
      <P>Hidayah is a place to read, search and learn from Islamic sources, with answers that always show where they came from.</P>
      <H2>How it works</H2>
      <P>Quran, hadith and dua texts are stored records from sources whose licences we have checked. They are never written by a model. The Ask feature retrieves passages from approved sources and explains them; if nothing relevant is found it says so.</P>
      <H2>What it is not</H2>
      <P>Hidayah does not give fatwas or personal rulings. Please ask a qualified scholar.</P>
      <P small>Privacy and terms text is still a draft pending legal review and is available on the website.</P>
    </Screen>
  )
}
