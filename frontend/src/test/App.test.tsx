import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/features/auth/AuthContext'
import { Header } from '@/layouts/Header'
import { LandingPage } from '@/pages/LandingPage'

describe('Landing page', () => {
  it('shows the headline and the question form', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByLabelText(/ask a question about islam/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ask' })).toBeInTheDocument()
  })

  it('does not invent religious content', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    // Daily verse and dua are honest empty states until verified data exists.
    expect(screen.getByText(/once the quran text and its translation sources/i)).toBeInTheDocument()
    expect(screen.getByText(/once supplications with checked references/i)).toBeInTheDocument()
  })
})

describe('Header', () => {
  it('toggles the mobile menu with correct aria state', async () => {
    render(
      <AuthContext.Provider
        value={{ status: 'anonymous', user: null, login: vi.fn(), register: vi.fn(), logout: vi.fn() }}
      >
        <MemoryRouter>
          <Header />
        </MemoryRouter>
      </AuthContext.Provider>,
    )
    const toggle = screen.getByRole('button', { name: /open menu/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(toggle)
    expect(screen.getByRole('button', { name: /close menu/i })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
  })
})
