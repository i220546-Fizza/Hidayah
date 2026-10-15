import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { ApiError } from '@/lib/api'

/** Shows loading and error states for a query; renders children only when data exists. */
export function Async<T>({ query, children }: { query: UseQueryResult<T>; children: (data: T) => ReactNode }) {
  if (query.isPending) return <p role="status" className="py-8 text-sm text-charcoal/80">Loading…</p>
  if (query.isError) {
    const msg = query.error instanceof ApiError ? query.error.message : 'Something went wrong.'
    return (
      <div role="alert" className="rounded-md border border-terracotta bg-white p-4 text-sm text-terracotta-deep">
        {msg}{' '}
        <button type="button" className="underline" onClick={() => void query.refetch()}>
          Try again
        </button>
      </div>
    )
  }
  return <>{children(query.data)}</>
}

export function PageHeading({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="mb-8">
      <h1 className="text-3xl sm:text-4xl">{title}</h1>
      {children && <p className="mt-3 max-w-prose text-charcoal/85">{children}</p>}
    </header>
  )
}
