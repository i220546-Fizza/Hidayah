import type { ReactNode } from 'react'

/** Form-level error from the server (for example "Incorrect email or password."). */
export function FormError({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div role="alert" className="rounded-md border border-terracotta bg-white p-3 text-sm text-terracotta-deep">
      <p className="font-medium">{title}</p>
      {children}
    </div>
  )
}
