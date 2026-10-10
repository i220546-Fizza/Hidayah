import { Hero } from '@/features/landing/Hero'
import { Areas, Daily, FinalCta, Reliability } from '@/features/landing/Sections'

export function LandingPage() {
  return (
    <>
      <Hero />
      <Areas />
      <Reliability />
      <Daily />
      <FinalCta />
    </>
  )
}
