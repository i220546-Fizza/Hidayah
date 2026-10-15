import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Async } from '@/components/content/Async'
import { Container } from '@/components/ui/Container'
import { EmptyState } from '@/components/ui/EmptyState'
import { api } from '@/lib/api'
import type { Source } from '@/lib/types'

function Doc({ title, draft, children }: { title: string; draft?: boolean; children: ReactNode }) {
  return (
    <Container className="max-w-3xl py-12">
      <h1 className="text-3xl sm:text-4xl">{title}</h1>
      {draft && (
        <p className="mt-4 rounded-md border border-bronze bg-white p-3 text-sm">
          Draft text. It has not yet been reviewed by a lawyer and will be replaced before public launch.
        </p>
      )}
      <div className="mt-6 space-y-4 [&_h2]:mt-8 [&_h2]:text-2xl [&_ul]:list-disc [&_ul]:pl-6">{children}</div>
    </Container>
  )
}

export function AboutPage() {
  return (
    <Doc title="About Hidayah">
      <p>Hidayah is a place to read, search and learn from Islamic sources, with answers that always show where they came from.</p>
      <h2>How it works</h2>
      <ul>
        <li>Quran, hadith and dua texts are stored records from sources whose licences we have checked. They are never written by a model.</li>
        <li>The Ask feature retrieves passages from approved sources and explains them. If nothing relevant is found it says so.</li>
        <li>Every text shows its source, edition and the credit its licence requires. See <Link to="/sources" className="underline">Sources and credits</Link>.</li>
      </ul>
      <h2>What it is not</h2>
      <p>Hidayah does not give fatwas or personal rulings. For those, please ask a qualified scholar.</p>
    </Doc>
  )
}

export function PrivacyPage() {
  return (
    <Doc title="Privacy" draft>
      <p>We keep the data needed to run your account and features you use.</p>
      <ul>
        <li>Account: email, optional name, a hashed password (never the password itself).</li>
        <li>Your activity: bookmarks, reading place, quiz attempts, and the questions you ask with their answers and feedback.</li>
        <li>Sessions: a sign-in cookie that scripts on the page cannot read.</li>
      </ul>
      <p>Questions you ask are sent to our answer provider (Anthropic) together with passages from our sources, so an answer can be written. Do not include personal details you would not want processed.</p>
      <p>You can download your data and delete your account from your account page.</p>
    </Doc>
  )
}

export function TermsPage() {
  return (
    <Doc title="Terms" draft>
      <p>Hidayah is a learning aid. It is provided as is, without a promise that it is complete or error-free.</p>
      <ul>
        <li>It does not give religious rulings. Consult a qualified scholar for personal questions.</li>
        <li>Source texts remain the property of their rights holders and are shown under the licences listed on the Sources page.</li>
        <li>Please do not misuse the service, attempt to access other people's data, or copy the content in bulk.</li>
      </ul>
    </Doc>
  )
}

export function ContactPage() {
  return (
    <Doc title="Contact">
      <p>A contact address has not been published yet. It will be added here before launch.</p>
    </Doc>
  )
}

export function SourcesPage() {
  const q = useQuery({ queryKey: ['public-sources'], queryFn: () => api<Source[]>('/sources') })
  return (
    <Doc title="Sources and credits">
      <p>Only sources that passed our licence and content review appear here. Content from any other source is never shown.</p>
      <Async query={q}>
        {(items) =>
          items.length === 0 ? (
            <EmptyState title="No sources are approved yet">
              We are verifying licences before importing anything. This list fills in as each source is approved.
            </EmptyState>
          ) : (
            <ul className="!list-none !pl-0 space-y-4">
              {items.map((s) => (
                <li key={s.slug} className="rounded-md border border-sand bg-white p-4">
                  <p className="font-display text-lg text-emerald">{s.title}</p>
                  <p className="text-sm">{[s.edition, s.author_or_publisher, s.translator && `Translator: ${s.translator}`].filter(Boolean).join(' · ')}</p>
                  {s.attribution_text && <p className="mt-1 text-sm">{s.attribution_text}</p>}
                  <p className="mt-1 text-sm">
                    {s.rights_holder && <>Rights holder: {s.rights_holder}. </>}
                    {s.license_name && (s.license_url ? <a className="text-emerald underline" href={s.license_url} target="_blank" rel="noreferrer noopener">{s.license_name}</a> : s.license_name)}
                  </p>
                  {s.original_url && <p className="text-sm"><a className="text-emerald underline" href={s.original_url} target="_blank" rel="noreferrer noopener">Original source</a></p>}
                </li>
              ))}
            </ul>
          )
        }
      </Async>
    </Doc>
  )
}
