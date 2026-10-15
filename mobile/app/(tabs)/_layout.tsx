import { Tabs } from 'expo-router'
import { colors, fonts } from '@/theme/tokens'

const tab = (title: string) => ({ title, tabBarIcon: () => null, tabBarLabelStyle: { fontFamily: fonts.sansMedium, fontSize: 13 } })

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{
      headerStyle: { backgroundColor: colors.ivory }, headerTintColor: colors.emerald, headerTitleStyle: { fontFamily: fonts.display },
      tabBarActiveTintColor: colors.emerald, tabBarInactiveTintColor: colors.charcoal, tabBarStyle: { backgroundColor: colors.ivory, borderTopColor: colors.sand },
    }}>
      <Tabs.Screen name="index" options={tab('Home')} />
      <Tabs.Screen name="quran" options={tab('Quran')} />
      <Tabs.Screen name="hadith" options={tab('Hadith')} />
      <Tabs.Screen name="duas" options={tab('Duas')} />
      <Tabs.Screen name="ask" options={tab('Ask')} />
      <Tabs.Screen name="more" options={tab('More')} />
    </Tabs>
  )
}
