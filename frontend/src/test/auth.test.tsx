import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '@/features/auth/AuthContext'
import { Header } from '@/layouts/Header'
import { ApiError } from '@/lib/api'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'

function ctx(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    status: 'anonymous',
    user: null,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }
}

function renderAt(path: string, value: AuthContextValue, ui: React.ReactNode) {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/" element={<p>Home page</p>} />
          <Route path={path} element={ui} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('LoginPage', () => {
  it('shows field errors and does not call the server for invalid input', async () => {
    const value = ctx()
    renderAt('/login', value, <LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
    expect(value.login).not.toHaveBeenCalled()
  })

  it('logs in and goes to the home page', async () => {
    const value = ctx()
    renderAt('/login', value, <LoginPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'correct-horse-battery')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    await waitFor(() => expect(value.login).toHaveBeenCalledWith('a@example.com', 'correct-horse-battery'))
    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })

  it('shows the server error in an alert', async () => {
    const value = ctx({ login: vi.fn().mockRejectedValue(new ApiError(401, 'Incorrect email or password.')) })
    renderAt('/login', value, <LoginPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password-1')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password.')
    expect(screen.queryByText('Home page')).not.toBeInTheDocument()
  })

  it('password field hides its text and has the right autocomplete hint', () => {
    renderAt('/login', ctx(), <LoginPage />)
    const field = screen.getByLabelText('Password')
    expect(field).toHaveAttribute('type', 'password')
    expect(field).toHaveAttribute('autocomplete', 'current-password')
  })

  it('redirects away when already signed in', async () => {
    renderAt('/login', ctx({ status: 'authenticated' }), <LoginPage />)
    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })
})

describe('RegisterPage', () => {
  it('requires a password of at least 10 characters before calling the server', async () => {
    const value = ctx()
    renderAt('/register', value, <RegisterPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Use at least 10 characters.', { selector: 'p[role="alert"]' })).toBeInTheDocument()
    expect(value.register).not.toHaveBeenCalled()
  })

  it('creates the account and goes home', async () => {
    const value = ctx()
    renderAt('/register', value, <RegisterPage />)
    await userEvent.type(screen.getByLabelText('Name (optional)'), 'Aisha')
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'a-long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await waitFor(() => expect(value.register).toHaveBeenCalledWith('a@example.com', 'a-long-enough-password', 'Aisha'))
    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })

  it('lists the server password problems', async () => {
    const value = ctx({
      register: vi.fn().mockRejectedValue(new ApiError(422, 'Choose a stronger password.', ['Password cannot be the same as your email.'])),
    })
    renderAt('/register', value, <RegisterPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'a-long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Choose a stronger password.')
    expect(alert).toHaveTextContent('Password cannot be the same as your email.')
  })

  it('shows a friendly message when the email is taken', async () => {
    const value = ctx({ register: vi.fn().mockRejectedValue(new ApiError(409, 'An account with this email already exists.')) })
    renderAt('/register', value, <RegisterPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'a-long-enough-password')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('already exists')
  })
})

describe('Header account area', () => {
  const user = { id: '1', email: 'a@example.com', display_name: 'Aisha', email_verified: false, roles: ['user'], created_at: '' }

  it('shows the name and a log out button when signed in', async () => {
    const value = ctx({ status: 'authenticated', user })
    renderAt('/x', value, <Header />)
    expect(screen.getAllByText('Aisha').length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: 'Create account' })).not.toBeInTheDocument()
    await userEvent.click(screen.getAllByRole('button', { name: 'Log out' })[0])
    expect(value.logout).toHaveBeenCalled()
  })

  it('shows log in and create account when signed out', () => {
    renderAt('/x', ctx(), <Header />)
    expect(screen.getAllByRole('link', { name: 'Log in' }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('link', { name: 'Create account' }).length).toBeGreaterThan(0)
  })

  it('shows neither while the session is still loading', () => {
    renderAt('/x', ctx({ status: 'loading' }), <Header />)
    expect(screen.queryByRole('link', { name: 'Log in' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Log out' })).not.toBeInTheDocument()
  })
})

describe('AuthProvider with a real client and mocked network', () => {
  const fetchMock = vi.fn()
  beforeEach(() => {
    vi.resetModules()
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  const json = (status: number, body: unknown) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

  it('resumes an existing session from the refresh cookie', async () => {
    const { AuthProvider: Provider } = await import('@/features/auth/AuthContext')
    const { useAuth: useAuthFresh } = await import('@/features/auth/useAuth')
    function FreshProbe() {
      const { status, user } = useAuthFresh()
      return <p>{status}:{user?.email ?? 'none'}</p>
    }
    fetchMock
      .mockResolvedValueOnce(json(200, { access_token: 'tok' }))
      .mockResolvedValueOnce(json(200, { id: '1', email: 'a@example.com', display_name: null, email_verified: false, roles: ['user'], created_at: '' }))
    render(<Provider><FreshProbe /></Provider>)
    expect(await screen.findByText('authenticated:a@example.com')).toBeInTheDocument()
  })

  it('is anonymous when there is no session', async () => {
    const { AuthProvider: Provider } = await import('@/features/auth/AuthContext')
    const { useAuth: useAuthFresh } = await import('@/features/auth/useAuth')
    function FreshProbe() {
      const { status } = useAuthFresh()
      return <p>{status}</p>
    }
    fetchMock.mockResolvedValue(json(401, { detail: 'Sign in again to continue.' }))
    render(<Provider><FreshProbe /></Provider>)
    expect(await screen.findByText('anonymous')).toBeInTheDocument()
  })

  it('does not fire two refresh calls under React StrictMode', async () => {
    const { StrictMode } = await import('react')
    const { AuthProvider: Provider } = await import('@/features/auth/AuthContext')
    fetchMock.mockResolvedValue(json(401, {}))
    render(<StrictMode><Provider><p>x</p></Provider></StrictMode>)
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    await new Promise((r) => setTimeout(r, 50))
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
  })

  it('logout forgets the session even if the server is unreachable', async () => {
    const { AuthProvider: Provider } = await import('@/features/auth/AuthContext')
    const { useAuth: useAuthFresh } = await import('@/features/auth/useAuth')
    function FreshProbe() {
      const { status, user, logout } = useAuthFresh()
      return (<><p>{status}:{user?.email ?? 'none'}</p><button onClick={() => void logout()}>out</button></>)
    }
    fetchMock
      .mockResolvedValueOnce(json(200, { access_token: 'tok' }))
      .mockResolvedValueOnce(json(200, { id: '1', email: 'a@example.com', display_name: null, email_verified: false, roles: [], created_at: '' }))
      .mockRejectedValueOnce(new TypeError('offline'))
    render(<Provider><FreshProbe /></Provider>)
    await screen.findByText('authenticated:a@example.com')
    await userEvent.click(screen.getByText('out'))
    expect(await screen.findByText('anonymous:none')).toBeInTheDocument()
  })
})
