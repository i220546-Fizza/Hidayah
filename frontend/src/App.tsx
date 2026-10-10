import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import { RootLayout } from '@/layouts/RootLayout'
import { LoginPage } from '@/pages/LoginPage'
import { LandingPage } from '@/pages/LandingPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { RegisterPage } from '@/pages/RegisterPage'

const placeholders = [
  { path: 'ask', title: 'Ask a question', phase: 'Phase 6 (assistant)' },
  { path: 'quran', title: 'Quran and tafsir', phase: 'Phase 7' },
  { path: 'hadith', title: 'Hadith', phase: 'Phase 7' },
  { path: 'duas', title: 'Duas', phase: 'Phase 7' },
  { path: 'learning', title: 'Learning', phase: 'Phase 7' },
  { path: 'about', title: 'About Hidayah', phase: 'Phase 7' },
  { path: 'privacy', title: 'Privacy', phase: 'Phase 10' },
  { path: 'terms', title: 'Terms', phase: 'Phase 10' },
  { path: 'contact', title: 'Contact', phase: 'Phase 10' },
  { path: 'sources', title: 'Sources and licensing', phase: 'Phase 5' },
]

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<RootLayout />}>
            <Route index element={<LandingPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            {placeholders.map((p) => (
              <Route
                key={p.path}
                path={p.path}
                element={<PlaceholderPage title={p.title} phase={p.phase} />}
              />
            ))}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
