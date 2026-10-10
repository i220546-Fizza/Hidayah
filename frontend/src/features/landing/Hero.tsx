import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { ArchPanel } from '@/components/brand/ArchPanel'
import { Button } from '@/components/ui/Button'
import { Container } from '@/components/ui/Container'

export function Hero() {
  const [question, setQuestion] = useState('')
  const navigate = useNavigate()

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
    navigate(q ? `/ask?q=${encodeURIComponent(q)}` : '/ask')
  }

  return (
    <section className="overflow-hidden">
      <Container className="grid items-center gap-10 py-14 md:grid-cols-[1.15fr_0.85fr] md:py-20">
        <div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl">
            Learn from the Quran, Hadith and duas, with every source in view.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-charcoal/85">
            Hidayah brings together the Quran, tafsir, hadith, supplications and structured
            lessons in English and Urdu. Each answer points back to the text it came from, so you
            can read it for yourself.
          </p>

          <form onSubmit={onSubmit} role="search" className="mt-8 max-w-xl">
            <label htmlFor="hero-question" className="mb-2 block text-sm font-medium text-emerald">
              Ask a question about Islam
            </label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search
                  size={18}
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-bronze"
                />
                <input
                  id="hero-question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="For example: what does the Quran say about patience?"
                  className="min-h-11 w-full rounded-md border border-sage bg-white py-2.5 pl-10 pr-3 text-sm placeholder:text-charcoal/75 focus:border-emerald"
                />
              </div>
              <Button type="submit">Ask</Button>
            </div>
            <p className="mt-3 text-xs text-charcoal/85">
              Answers cite approved sources and can be wrong. For personal rulings, ask a
              qualified scholar.
            </p>
          </form>
        </div>

        <ArchPanel className="mx-auto hidden h-auto w-full max-w-sm md:block" />
      </Container>
    </section>
  )
}
