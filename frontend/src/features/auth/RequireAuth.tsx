import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Container } from '@/components/ui/Container'
import { useAuth } from './useAuth'

/** Page-level guard for convenience only. The server checks every request itself. */
export function RequireAuth({ role }: { role?: string }) {
  const { status, user } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <Container className="py-16"><p role="status">Loading…</p></Container>
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (role && !user?.roles.includes(role)) {
    return (
      <Container className="py-16">
        <h1 className="text-3xl">Not allowed</h1>
        <p className="mt-3">Your account does not have access to this page.</p>
      </Container>
    )
  }
  return <Outlet />
}
