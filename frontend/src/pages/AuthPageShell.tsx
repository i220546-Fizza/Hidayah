import type { ReactNode } from 'react'
import { Emblem } from '@/components/brand/Emblem'
import { Container } from '@/components/ui/Container'

export function AuthPageShell({ title, intro, children }: { title: string; intro: string; children: ReactNode }) {
  return (
    <Container className="grid items-start gap-10 py-14 md:grid-cols-[1fr_1fr] md:py-20">
      <div className="max-w-md">
        <Emblem className="mb-5 h-12 w-12 text-emerald" />
        <h1 className="text-3xl sm:text-4xl">{title}</h1>
        <p className="mt-3 text-charcoal/85">{intro}</p>
      </div>
      <div className="w-full max-w-md rounded-md border border-sand bg-white p-6 shadow-card sm:p-8">{children}</div>
    </Container>
  )
}
