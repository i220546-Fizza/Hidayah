import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { useAuth } from '@/features/auth/useAuth'
import { loginSchema, type LoginValues } from '@/features/auth/schemas'
import { ApiError } from '@/lib/api'
import { AuthPageShell } from './AuthPageShell'

export function LoginPage() {
  const { status, login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  if (status === 'authenticated') return <Navigate to="/" replace />

  const onSubmit = handleSubmit(async ({ email, password }) => {
    setServerError(null)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : 'Something went wrong. Try again.')
    }
  })

  return (
    <AuthPageShell title="Welcome back" intro="Log in to see your bookmarks, conversations and progress on any device.">
      <form onSubmit={onSubmit} noValidate className="space-y-5">
        {serverError && <FormError title={serverError} />}
        <TextField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Logging in' : 'Log in'}
        </Button>
        <p className="text-sm">
          <Link to="/forgot-password" className="font-medium text-emerald underline underline-offset-4">
            Forgot your password?
          </Link>
        </p>
        <p className="text-sm text-charcoal/85">
          New to Hidayah?{' '}
          <Link to="/register" className="font-medium text-emerald underline underline-offset-4">
            Create an account
          </Link>
        </p>
      </form>
    </AuthPageShell>
  )
}
