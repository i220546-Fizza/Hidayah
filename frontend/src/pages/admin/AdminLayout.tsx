import { NavLink, Outlet } from 'react-router-dom'
import { Container } from '@/components/ui/Container'

const tabs = [
  { to: '/admin', label: 'Overview', end: true },
  { to: '/admin/sources', label: 'Sources' },
  { to: '/admin/learning', label: 'Learning' },
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/audit', label: 'Audit log' },
]

export function AdminLayout() {
  return (
    <Container className="py-10">
      <h1 className="text-3xl">Admin</h1>
      <nav aria-label="Admin sections" className="mt-4 flex flex-wrap gap-1 border-b border-sand pb-2">
        {tabs.map((t) => (
          <NavLink key={t.to} to={t.to} end={t.end}
            className={({ isActive }) => `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-sand text-emerald' : 'hover:bg-sand/70'}`}>
            {t.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-8"><Outlet /></div>
    </Container>
  )
}
