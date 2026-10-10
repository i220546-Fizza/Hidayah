import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { useAuth } from '@/features/auth/useAuth'
import { registerSchema, type RegisterValues } from '@/features/auth/schemas'
import { ApiError } from '@/lib/api'
import { AuthPageShell } from './AuthPageShell'

export function RegisterPage() {
  const { status, register: signUp } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<{ message: string; details: string[] } | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  if (status === 'authenticated') return <Navigate to="/" replace />

  const onSubmit = handleSubmit(async ({ email, password, displayName }) => {
    setServerError(null)
    try {
      await signUp(email, password, displayName?.trim())
      navigate('/', { replace: true })
    } catch (e) {
      setServerError(
        e instanceof ApiError
          ? { message: e.message, details: e.details }
          : { message: 'Something went wrong. Try again.', details: [] },
      )
    }
  })

  return (
    <AuthPageShell
      title="Create your account"
      intro="An account keeps your bookmarks, saved conversations and learning progress in sync between the website and the app. You can explore without one."
    >
      <form onSubmit={onSubmit} noValidate className="space-y-5">
        {serverError && (
          <FormError title={serverError.message}>
            {serverError.details.length > 0 && (
              <ul className="mt-1 list-disc pl-5">
                {serverError.details.map((d) => (
                  <li key={d}>{d}</li>
                ))}
              </ul>
            )}
          </FormError>
        )}
        <TextField
          label="Name (optional)"
          autoComplete="name"
          error={errors.displayName?.message}
          {...register('displayName')}
        />
        <TextField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          hint="At least 10 characters."
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account' : 'Create account'}
        </Button>
        <p className="text-sm text-charcoal/85">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-emerald underline underline-offset-4">
            Log in
          </Link>
        </p>
      </form>
    </AuthPageShell>
  )
}
