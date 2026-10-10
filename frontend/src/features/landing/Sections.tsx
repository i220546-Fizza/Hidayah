import { Link } from 'react-router-dom'
import { ButtonLink } from '@/components/ui/Button'
import { Container } from '@/components/ui/Container'
import { EmptyState } from '@/components/ui/EmptyState'

const areas = [
  {
    to: '/quran',
    title: 'Quran and tafsir',
    body: 'Read each surah verse by verse in Arabic, with translations and tafsir you can switch between. Text size is yours to set.',
  },
  {
    to: '/hadith',
    title: 'Hadith',
    body: 'Search recognized collections by phrase or topic. Every narration shows its collection, book and number, and any documented grading with who gave it.',
  },
  {
    to: '/duas',
    title: 'Duas',
    body: 'Find supplications by purpose, with Arabic, transliteration, translation and the reference each one comes from.',
  },
  {
    to: '/learning',
    title: 'Learning paths',
    body: 'Work through beginner to advanced topics, check yourself with quizzes, and pick up where you stopped.',
  },
]

export function Areas() {
  return (
    <section className="border-t border-sand bg-white py-16" aria-labelledby="areas-heading">
      <Container>
        <h2 id="areas-heading" className="max-w-2xl text-3xl sm:text-4xl">
          Four places to start
        </h2>
        <ul className="mt-10 divide-y divide-sand border-y border-sand">
          {areas.map((a) => (
            <li key={a.to}>
              <Link
                to={a.to}
                className="grid gap-2 py-6 transition-colors hover:bg-ivory sm:grid-cols-[14rem_1fr] sm:gap-8 sm:px-3"
              >
                <span className="font-display text-xl font-semibold text-emerald">{a.title}</span>
                <span className="max-w-prose text-charcoal/85">{a.body}</span>
              </Link>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  )
}

export function Reliability() {
  return (
    <section className="bg-emerald py-16 text-ivory" aria-labelledby="reliability-heading">
      <Container className="grid gap-10 md:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h2 id="reliability-heading" className="text-3xl text-ivory sm:text-4xl">
            How we treat sources
          </h2>
          <p className="mt-4 max-w-md text-ivory/85">
            Religious knowledge needs care. These are the rules the platform is built around.
          </p>
        </div>
        <ul className="space-y-6">
          <li>
            <h3 className="font-display text-xl text-gold">Sacred text is never generated</h3>
            <p className="mt-1 text-ivory/85">
              Quranic verses, hadith and duas come from stored, verified records. The assistant
              can quote them but cannot write or reword them.
            </p>
          </li>
          <li>
            <h3 className="font-display text-xl text-gold">Only approved sources are searched</h3>
            <p className="mt-1 text-ivory/85">
              A source must pass review, with its edition and license recorded, before it can
              inform an answer.
            </p>
          </li>
          <li>
            <h3 className="font-display text-xl text-gold">Uncertainty is stated</h3>
            <p className="mt-1 text-ivory/85">
              When the evidence is thin or scholars differ, the answer says so. When there is not
              enough to go on, it declines rather than guesses.
            </p>
          </li>
        </ul>
      </Container>
    </section>
  )
}

export function Daily() {
  return (
    <section className="py-16" aria-labelledby="daily-heading">
      <Container>
        <h2 id="daily-heading" className="max-w-2xl text-3xl sm:text-4xl">
          A small daily practice
        </h2>
        <p className="mt-4 max-w-xl text-charcoal/85">
          Each day Hidayah will show one verse and one dua with their references, a short
          reflection, and a quiz question. Reminders are optional and only sent if you turn them on.
        </p>
        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <EmptyState title="Today's verse">
            Shown here once the Quran text and its translation sources have been verified and
            approved.
          </EmptyState>
          <EmptyState title="Featured dua">
            Shown here once supplications with checked references have been added.
          </EmptyState>
        </div>
      </Container>
    </section>
  )
}

export function FinalCta() {
  return (
    <section className="border-t border-sand bg-sand/60 py-16">
      <Container className="flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-xl">
          <h2 className="text-3xl">Keep your place, wherever you read</h2>
          <p className="mt-3 text-charcoal/85">
            An account saves your bookmarks, conversations and learning progress across the
            website and the mobile app. You can explore without one.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <ButtonLink to="/register">Create account</ButtonLink>
          <ButtonLink to="/quran" variant="secondary">
            Explore without an account
          </ButtonLink>
        </div>
      </Container>
    </section>
  )
}
