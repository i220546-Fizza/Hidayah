import type { ReactNode } from 'react'

/**
 * Honest placeholder for content that must come from a verified, approved
 * source. We never fill these with invented religious text.
 */
export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-sage bg-ivory p-6">
      <p className="font-display text-lg font-semibold text-emerald">{title}</p>
      <p className="mt-2 max-w-prose text-sm text-charcoal/80">{children}</p>
    </div>
  )
}
