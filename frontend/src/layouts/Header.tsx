import { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { Logo } from '@/components/brand/Logo'
import { ButtonLink } from '@/components/ui/Button'
import { Container } from '@/components/ui/Container'
import { navItems } from './navItems'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-sand text-emerald' : 'text-charcoal hover:bg-sand/70'
  }`

export function Header() {
  // The menu is "open" only for the page it was opened on, so navigating
  // to another page closes it without needing an effect.
  const { pathname } = useLocation()
  const [openOn, setOpenOn] = useState<string | null>(null)
  const open = openOn === pathname

  return (
    <header className="sticky top-0 z-40 border-b border-sand bg-ivory/95 backdrop-blur">
      <Container className="flex h-16 items-center justify-between">
        <Link to="/" aria-label="Hidayah home">
          <Logo />
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={'end' in item} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <ButtonLink to="/login" variant="quiet">
            Log in
          </ButtonLink>
          <ButtonLink to="/register">Create account</ButtonLink>
        </div>

        <button
          type="button"
          className="inline-flex h-11 w-11 items-center justify-center rounded-md text-emerald hover:bg-sand lg:hidden"
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? 'Close menu' : 'Open menu'}
          onClick={() => setOpenOn(open ? null : pathname)}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </Container>

      {open && (
        <nav
          id="mobile-menu"
          aria-label="Main"
          className="border-t border-sand bg-ivory lg:hidden"
        >
          <Container className="flex flex-col gap-1 py-3">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={'end' in item} className={linkClass}>
                {item.label}
              </NavLink>
            ))}
            <div className="mt-2 grid grid-cols-2 gap-2">
              <ButtonLink to="/login" variant="secondary">
                Log in
              </ButtonLink>
              <ButtonLink to="/register">Create account</ButtonLink>
            </div>
          </Container>
        </nav>
      )}
    </header>
  )
}
