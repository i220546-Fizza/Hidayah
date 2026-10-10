import { forwardRef, useId, type InputHTMLAttributes } from 'react'

type Props = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }

export const TextField = forwardRef<HTMLInputElement, Props>(function TextField(
  { label, error, hint, className = '', ...props },
  ref,
) {
  const id = useId()
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(' ')
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-charcoal">
        {label}
      </label>
      <input
        id={id}
        ref={ref}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
        className={`min-h-11 w-full rounded-md border bg-white px-3 py-2.5 text-sm placeholder:text-charcoal/75 focus:border-emerald ${
          error ? 'border-terracotta' : 'border-sage'
        } ${className}`}
        {...props}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-charcoal/85">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs font-medium text-terracotta-deep">
          {error}
        </p>
      )}
    </div>
  )
})
