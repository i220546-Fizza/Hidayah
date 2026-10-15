import { ExternalLink } from 'lucide-react'
import type { Source } from '@/lib/types'

/** Every piece of religious text is shown with where it came from. */
export function SourceCredit({ source, label }: { source: Source | null; label?: string }) {
  if (!source) return null
  const parts = [source.title, source.edition, source.translator ? `tr. ${source.translator}` : null].filter(Boolean)
  return (
    <p className="mt-2 text-xs text-charcoal/80">
      {label ? `${label}: ` : 'Source: '}
      {parts.join(' · ')}
      {source.attribution_text ? ` — ${source.attribution_text}` : source.rights_holder ? ` — ${source.rights_holder}` : ''}
      {source.license_url && (
        <>
          {' '}
          <a href={source.license_url} className="inline-flex items-center gap-1 text-emerald underline" target="_blank" rel="noreferrer noopener">
            {source.license_name ?? 'Licence'} <ExternalLink size={11} aria-hidden />
          </a>
        </>
      )}
    </p>
  )
}
