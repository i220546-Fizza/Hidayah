import { Emblem } from './Emblem'

type LogoProps = {
  /** "light" = dark text for ivory/white backgrounds. "dark" = light text for emerald. */
  tone?: 'light' | 'dark'
  className?: string
}

export function Logo({ tone = 'light', className = '' }: LogoProps) {
  const text = tone === 'light' ? 'text-emerald' : 'text-ivory'
  const accent = tone === 'light' ? 'text-bronze' : 'text-gold'

  return (
    <span className={`inline-flex items-center gap-3 ${className}`}>
      <Emblem className={`h-9 w-9 ${text}`} />
      <span className="flex flex-col leading-none">
        <span className={`font-display text-xl font-semibold tracking-wide ${text}`}>
          HIDAYAH
        </span>
        <span lang="ar" className={`arabic mt-1 text-base leading-none ${accent}`}>
          هداية
        </span>
      </span>
    </span>
  )
}
