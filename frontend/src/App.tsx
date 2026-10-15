import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { RootLayout } from '@/layouts/RootLayout'
import { AccountPage } from '@/pages/AccountPage'
import { AskPage } from '@/pages/AskPage'
import { CollectionPage, DuasPage, HadithDetailPage, HadithPage } from '@/pages/HadithDuaPages'
import { AboutPage, ContactPage, PrivacyPage, SourcesPage, TermsPage } from '@/pages/InfoPages'
import { ForgotPasswordPage, ResetPasswordPage, VerifyEmailPage } from '@/pages/EmailPages'
import { LandingPage } from '@/pages/LandingPage'
import { LearningPage, PathPage, QuizPage } from '@/pages/LearningPages'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { QuranPage, SurahPage } from '@/pages/QuranPages'
import { RegisterPage } from '@/pages/RegisterPage'
import { SearchPage } from '@/pages/SearchPage'
import { AdminLayout } from '@/pages/admin/AdminLayout'
import { AdminAudit, AdminLearning, AdminOverview, AdminSourceDetail, AdminSources, AdminUsers } from '@/pages/admin/AdminPages'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<RootLayout />}>
              <Route index element={<LandingPage />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
              <Route path="reset-password" element={<ResetPasswordPage />} />
              <Route path="verify-email" element={<VerifyEmailPage />} />
              <Route path="ask" element={<AskPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="quran" element={<QuranPage />} />
              <Route path="quran/:number" element={<SurahPage />} />
              <Route path="hadith" element={<HadithPage />} />
              <Route path="hadith/collections/:slug" element={<CollectionPage />} />
              <Route path="hadith/:id" element={<HadithDetailPage />} />
              <Route path="duas" element={<DuasPage />} />
              <Route path="learning" element={<LearningPage />} />
              <Route path="learning/paths/:slug" element={<PathPage />} />
              <Route path="learning/quizzes/:id" element={<QuizPage />} />
              <Route path="about" element={<AboutPage />} />
              <Route path="privacy" element={<PrivacyPage />} />
              <Route path="terms" element={<TermsPage />} />
              <Route path="contact" element={<ContactPage />} />
              <Route path="sources" element={<SourcesPage />} />
              <Route element={<RequireAuth />}>
                <Route path="account" element={<AccountPage />} />
              </Route>
              <Route element={<RequireAuth role="admin" />}>
                <Route path="admin" element={<AdminLayout />}>
                  <Route index element={<AdminOverview />} />
                  <Route path="sources" element={<AdminSources />} />
                  <Route path="sources/:id" element={<AdminSourceDetail />} />
                  <Route path="learning" element={<AdminLearning />} />
                  <Route path="users" element={<AdminUsers />} />
                  <Route path="audit" element={<AdminAudit />} />
                </Route>
              </Route>
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
