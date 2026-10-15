import { Amiri_400Regular } from '@expo-google-fonts/amiri'
import { Inter_400Regular, Inter_500Medium } from '@expo-google-fonts/inter'
import { PlayfairDisplay_600SemiBold } from '@expo-google-fonts/playfair-display'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useFonts } from 'expo-font'
import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { StatusBar } from 'expo-status-bar'
import { useEffect } from 'react'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { AuthProvider } from '@/auth/AuthContext'
import { colors } from '@/theme/tokens'

void SplashScreen.preventAutoHideAsync()
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30_000 } } })

export default function RootLayout() {
  const [loaded, error] = useFonts({ Amiri_400Regular, Inter_400Regular, Inter_500Medium, PlayfairDisplay_600SemiBold })
  useEffect(() => {
    if (loaded || error) void SplashScreen.hideAsync() // show text in a system font if a font fails to load
  }, [loaded, error])
  if (!loaded && !error) return null
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerStyle: { backgroundColor: colors.ivory }, headerTintColor: colors.emerald, contentStyle: { backgroundColor: colors.ivory }, headerTitleStyle: { fontFamily: 'PlayfairDisplay_600SemiBold' } }}>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          </Stack>
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  )
}
