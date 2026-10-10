import { ButtonLink } from '@/components/ui/Button'
import { Container } from '@/components/ui/Container'

export function NotFoundPage() {
  return (
    <Container className="py-20">
      <h1 className="text-4xl">Page not found</h1>
      <p className="mt-4 max-w-prose text-charcoal/85">
        We could not find that address. Check it for typing mistakes, or go back to the home page.
      </p>
      <ButtonLink to="/" variant="secondary" className="mt-8">
        Back to home
      </ButtonLink>
    </Container>
  )
}
