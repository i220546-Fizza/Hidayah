import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '@/features/auth/AuthContext'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { AskPage } from '@/pages/AskPage'
import { DuasPage, HadithPage } from '@/pages/HadithDuaPages'
import { SourcesPage } from '@/pages/InfoPages'
import { QuizPage } from '@/pages/LearningPages'
import { QuranPage, SurahPage } from '@/pages/QuranPages'

const fetchMock = vi.fn()
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
// A Response body can be read once, so every call needs a fresh one.
const reply = (body: unknown, status = 200) => fetchMock.mockImplementation(() => Promise.resolve(json(body, status)))

const source = { slug: 's', title: 'Test Source', category: 'x', language: 'en', author_or_publisher: null, translator: null,
  edition: 'Test edition', rights_holder: 'Test Holder', license_name: null, license_url: null, attribution_text: 'Credit line', original_url: null }

function auth(over: Partial<AuthContextValue> = {}): AuthContextValue {
  return { status: 'anonymous', user: null, login: vi.fn(), register: vi.fn(), logout: vi.fn(), ...over }
}

function mount(path: string, element: React.ReactNode, routePath = path, value = auth()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AuthContext.Provider value={value}>
        <MemoryRouter initialEntries={[path]}>
          <Routes><Route path={routePath} element={element} /></Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

beforeEach(() => { fetchMock.mockReset(); vi.stubGlobal('fetch', fetchMock) })
afterEach(() => vi.unstubAllGlobals())

describe('empty states are honest', () => {
  it('Quran: says no text is available instead of inventing any', async () => {
    reply([])
    mount('/quran', <QuranPage />)
    expect(await screen.findByText('The Quran text is not available yet')).toBeInTheDocument()
  })
  it('Hadith, Duas, Sources', async () => {
    reply([])
    mount('/hadith', <HadithPage />)
    expect(await screen.findByText('No hadith collections are available yet')).toBeInTheDocument()
    mount('/duas', <DuasPage />)
    expect(await screen.findByText('No duas are available yet')).toBeInTheDocument()
    mount('/sources', <SourcesPage />)
    expect(await screen.findByText('No sources are approved yet')).toBeInTheDocument()
  })
})

describe('Surah page', () => {
  it('shows Arabic, translation and a credit for each', async () => {
    reply({
      surah: { number: 1, name_arabic: 'TEST-AR', name_english: 'Test One', name_transliterated: null, verse_count: 1 },
      verses: [{ surah_number: 1, verse_number: 1, text_arabic: 'TEST-ARABIC', source, translations: [{ language: 'en', text: 'TEST translation', source }] }],
      total: 1, limit: 50, offset: 0,
    })
    mount('/quran/1', <SurahPage />, '/quran/:number')
    expect(await screen.findByText('TEST-ARABIC')).toHaveAttribute('lang', 'ar')
    expect(screen.getByText('TEST translation')).toBeInTheDocument()
    expect(screen.getAllByText(/Credit line/).length).toBe(2)
  })
  it('shows an error with retry when the server fails', async () => {
    reply({ detail: 'Surah not found.' }, 404)
    mount('/quran/9', <SurahPage />, '/quran/:number')
    expect(await screen.findByRole('alert')).toHaveTextContent('Surah not found.')
  })
})

describe('Ask page', () => {
  it('asks anonymous visitors to log in', () => {
    mount('/ask', <AskPage />)
    expect(screen.getByRole('link', { name: 'log in' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Your question')).not.toBeInTheDocument()
  })
  it('shows the answer with its sources and the disclaimer', async () => {
    reply({
      conversation_id: 'c1', disclaimer: 'Not a fatwa.',
      message: { id: 1, role: 'assistant', content: 'Answer text [E1]', outcome: 'answered', created_at: '', citations: [
        { kind: 'hadith', label: 'Test coll #1', text: 'TEST hadith text', text_arabic: null, link: '/hadith/1', source }] },
    })
    mount('/ask', <AskPage />, '/ask', auth({ status: 'authenticated' }))
    await userEvent.type(screen.getByLabelText('Your question'), 'What about kindness?')
    await userEvent.click(screen.getByRole('button', { name: 'Ask' }))
    expect(await screen.findByText('Answer text [E1]')).toBeInTheDocument()
    expect(screen.getByText('TEST hadith text')).toBeInTheDocument()
    expect(screen.getByText('Not a fatwa.')).toBeInTheDocument()
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string)
    expect(body.question).toBe('What about kindness?')
  })
  it('shows the not-switched-on message from the server', async () => {
    reply({ detail: 'The answer assistant is not switched on yet.' }, 503)
    mount('/ask', <AskPage />, '/ask', auth({ status: 'authenticated' }))
    await userEvent.type(screen.getByLabelText('Your question'), 'Anything at all')
    await userEvent.click(screen.getByRole('button', { name: 'Ask' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('not switched on')
  })
})

describe('Quiz page', () => {
  const quiz = { id: 1, title: 'Test quiz', topic: null, difficulty: 'beginner', question_count: 1,
    questions: [{ id: 5, prompt: 'Test question?', options: [{ id: 10, text: 'Wrong' }, { id: 11, text: 'Right' }] }] }
  it('submits answers and shows the score and explanation', async () => {
    fetchMock.mockImplementation((url: string) =>
      Promise.resolve(String(url).endsWith('/submit')
        ? json({ attempt_id: 1, score: 1, total: 1, results: [{ question_id: 5, chosen_option_id: 11, correct_option_id: 11, is_correct: true,
            explanation: { text: 'Because test.', reference_text: 'TEST ref', source } }] })
        : json(quiz)))
    mount('/learning/quizzes/1', <QuizPage />, '/learning/quizzes/:id', auth({ status: 'authenticated' }))
    await userEvent.click(await screen.findByLabelText('Right'))
    await userEvent.click(screen.getByRole('button', { name: 'Submit answers' }))
    expect(await screen.findByText('You scored 1 of 1.')).toBeInTheDocument()
    expect(screen.getByText('Because test.')).toBeInTheDocument()
    const sent = fetchMock.mock.calls.find(([u]) => String(u).endsWith('/submit'))!
    expect(JSON.parse(sent[1].body as string)).toEqual({ answers: { '5': 11 } })
  })
  it('asks anonymous people to log in before submitting', async () => {
    reply(quiz)
    mount('/learning/quizzes/1', <QuizPage />, '/learning/quizzes/:id')
    await screen.findByText('Test quiz')
    expect(screen.queryByRole('button', { name: 'Submit answers' })).not.toBeInTheDocument()
  })
})

describe('RequireAuth', () => {
  function guarded(value: AuthContextValue, role?: string) {
    return render(
      <AuthContext.Provider value={value}>
        <MemoryRouter initialEntries={['/secret']}>
          <Routes>
            <Route path="/login" element={<p>Login page</p>} />
            <Route element={<RequireAuth role={role} />}><Route path="/secret" element={<p>Secret</p>} /></Route>
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )
  }
  const user = (roles: string[]) => ({ id: '1', email: 'a@example.com', display_name: null, email_verified: false, roles, created_at: '' })
  it('sends anonymous visitors to log in', () => { guarded(auth()); expect(screen.getByText('Login page')).toBeInTheDocument() })
  it('waits while the session is loading', () => { guarded(auth({ status: 'loading' })); expect(screen.queryByText('Secret')).not.toBeInTheDocument() })
  it('lets a signed-in user through', () => { guarded(auth({ status: 'authenticated', user: user(['user']) })); expect(screen.getByText('Secret')).toBeInTheDocument() })
  it('blocks a non-admin from an admin route', async () => {
    guarded(auth({ status: 'authenticated', user: user(['user']) }), 'admin')
    await waitFor(() => expect(screen.getByText('Not allowed')).toBeInTheDocument())
    expect(screen.queryByText('Secret')).not.toBeInTheDocument()
  })
  it('lets an admin through', () => { guarded(auth({ status: 'authenticated', user: user(['admin']) }), 'admin'); expect(screen.getByText('Secret')).toBeInTheDocument() })
})

describe('Email pages', () => {
  it('reset page posts the token and new password', async () => {
    const { ResetPasswordPage } = await import('@/pages/EmailPages')
    fetchMock.mockImplementation(() => Promise.resolve(new Response(null, { status: 204 })))
    mount('/reset-password?token=abcdefghij1234', <ResetPasswordPage />, '/reset-password')
    await userEvent.type(screen.getByLabelText('New password'), 'a-long-new-password')
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByText(/Your password was changed/)).toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ token: 'abcdefghij1234', new_password: 'a-long-new-password' })
  })
  it('verify page shows the server error for a bad link', async () => {
    const { VerifyEmailPage } = await import('@/pages/EmailPages')
    reply({ detail: 'This link is invalid or has expired. Please request a new one.' }, 401)
    mount('/verify-email?token=abcdefghij1234', <VerifyEmailPage />, '/verify-email')
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })
  it('forgot page gives the same message either way', async () => {
    const { ForgotPasswordPage } = await import('@/pages/EmailPages')
    fetchMock.mockImplementation(() => Promise.resolve(new Response(null, { status: 204 })))
    mount('/forgot-password', <ForgotPasswordPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Send reset link' }))
    expect(await screen.findByText(/If an account exists/)).toBeInTheDocument()
  })
})

describe('Admin quiz builder', () => {
  it('sends a quiz with exactly one correct option', async () => {
    const { QuizBuilder } = await import('@/pages/admin/Authoring')
    fetchMock.mockImplementation((_url: string, init?: RequestInit) =>
      Promise.resolve(init?.method === 'POST' ? json({ id: 1 }, 201) : json({ items: [{ id: 4, title: 'Approved source' }], total: 1, limit: 100, offset: 0 })))
    mount('/x', <QuizBuilder />)
    await userEvent.type(screen.getByLabelText('Title'), 'My test quiz')
    await userEvent.type(screen.getByLabelText('Question text'), 'Which one?')
    await userEvent.type(screen.getByLabelText('Option 1'), 'First')
    await userEvent.type(screen.getByLabelText('Option 2'), 'Second')
    await userEvent.click(screen.getAllByRole('radio')[1])
    await userEvent.type(screen.getByLabelText('Explanation'), 'Because')
    await screen.findByRole('option', { name: 'Approved source' })
    await userEvent.selectOptions(screen.getByLabelText('Supporting approved source'), '4')
    await userEvent.click(screen.getByRole('button', { name: 'Save quiz as draft' }))
    await screen.findByText('Quiz saved as a draft.')
    const post = fetchMock.mock.calls.find(([, i]) => i?.method === 'POST')!
    const body = JSON.parse(post[1].body as string)
    expect(body.questions[0].options).toEqual([{ text: 'First', is_correct: false }, { text: 'Second', is_correct: true }])
    expect(body.questions[0].explanation.source_id).toBe(4)
  })
})
