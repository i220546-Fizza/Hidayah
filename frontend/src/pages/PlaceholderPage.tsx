import { ButtonLink } from '@/components/ui/Button'
import { Container } from '@/components/ui/Container'

/** Shown for sections that are planned but not built yet. */
export function PlaceholderPage({ title, phase }: { title: string; phase: string }) {
  return (
    <Container className="py-20">
      <h1 className="text-4xl">{title}</h1>
      <p className="mt-4 max-w-prose text-charcoal/85">
        This section has not been built yet. It is planned for {phase}.
      </p>
      <ButtonLink to="/" variant="secondary" className="mt-8">
        Back to home
      </ButtonLink>
    </Container>
  )
}
