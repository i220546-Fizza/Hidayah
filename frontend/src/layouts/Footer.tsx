import { Link } from 'react-router-dom'
import { Logo } from '@/components/brand/Logo'
import { Container } from '@/components/ui/Container'

const footerLinks = [
  { to: '/privacy', label: 'Privacy' },
  { to: '/terms', label: 'Terms' },
  { to: '/contact', label: 'Contact' },
  { to: '/sources', label: 'Sources and licensing' },
]

const currentYear = new Date().getFullYear()

export function Footer() {
  return (
    <footer className="bg-emerald text-ivory">
      <Container className="grid gap-8 py-12 md:grid-cols-[1.2fr_1fr]">
        <div>
          <Logo tone="dark" />
          <p className="mt-4 max-w-sm text-sm text-ivory/80">
            A path to knowledge, faith and guidance. Hidayah is a learning aid and does not
            replace a qualified scholar.
          </p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap content-start gap-x-6 gap-y-3 md:justify-end">
          {footerLinks.map((l) => (
            <Link key={l.to} to={l.to} className="text-sm text-ivory/90 underline-offset-4 hover:underline">
              {l.label}
            </Link>
          ))}
        </nav>
      </Container>
      <div className="border-t border-ivory/15">
        <Container className="py-4 text-xs text-ivory/70">
          © {currentYear} Hidayah. Religious texts shown on this site are credited to
          their sources and used under each source's license.
        </Container>
      </div>
    </footer>
  )
}
