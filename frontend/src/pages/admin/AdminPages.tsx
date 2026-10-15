import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Async } from '@/components/content/Async'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FormError } from '@/components/ui/FormMessage'
import { TextField } from '@/components/ui/TextField'
import { ApiError, api } from '@/lib/api'
import type { AdminSource, AuditEvent, Page, Readiness, Review, Stats } from '@/lib/types'
import type { User } from '@/features/auth/types'
import { PathBuilder, QuizBuilder } from './Authoring'

const errText = (e: unknown) => (e instanceof ApiError ? [e.message, ...e.details].join(' ') : e ? 'Something went wrong.' : null)

export function AdminOverview() {
  const q = useQuery({ queryKey: ['admin-stats'], queryFn: () => api<Stats>('/admin/stats', { auth: true }) })
  return (
    <Async query={q}>
      {(s) => (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card><p className="text-sm">Users</p><p className="font-display text-3xl">{s.users}</p></Card>
          <Card><p className="text-sm">Conversations</p><p className="font-display text-3xl">{s.conversations}</p></Card>
          <Card><p className="text-sm">Imported source versions</p><p className="font-display text-3xl">{s.source_versions}</p></Card>
          <Card className="sm:col-span-2">
            <p className="text-sm">Sources by status</p>
            <ul className="mt-2 grid grid-cols-2 gap-1 text-sm">{Object.entries(s.sources_by_status).map(([k, v]) => <li key={k}>{k.replace('_', ' ')}: <strong>{v}</strong></li>)}</ul>
          </Card>
          <Card>
            <p className="text-sm">Answer outcomes</p>
            <ul className="mt-2 text-sm">{Object.entries(s.answer_outcomes).map(([k, v]) => <li key={k}>{k.replace('_', ' ')}: <strong>{v}</strong></li>)}</ul>
            <p className="mt-2 text-sm">Feedback: {s.feedback_up} helpful, {s.feedback_down} not helpful</p>
          </Card>
          <Card><p className="text-sm">Approved quizzes / paths</p><p className="font-display text-3xl">{s.quizzes_approved} / {s.paths_approved}</p></Card>
        </div>
      )}
    </Async>
  )
}

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draft', candidate: 'Candidate', pending_permission: 'Waiting for permission', restricted: 'Restricted',
  under_review: 'Under review', approved: 'Approved', rejected: 'Rejected', archived: 'Archived',
}

export function AdminSources() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['admin-sources'], queryFn: () => api<Page<AdminSource>>('/admin/sources?limit=100', { auth: true }) })
  const [form, setForm] = useState({ slug: '', title: '', category: 'quran_text', language: 'ar' })
  const create = useMutation({
    mutationFn: () => api('/admin/sources', { method: 'POST', auth: true, json: form }),
    onSuccess: () => { setForm({ ...form, slug: '', title: '' }); void qc.invalidateQueries({ queryKey: ['admin-sources'] }) },
  })
  return (
    <>
      <Async query={q}>
        {(p) => p.items.length === 0 ? <EmptyState title="No sources registered">Register a source below before importing anything.</EmptyState> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Registered sources</caption>
              <thead><tr className="border-b border-sand"><th className="py-2 pr-4">Title</th><th className="pr-4">Category</th><th className="pr-4">Status</th><th>Commercial use</th></tr></thead>
              <tbody>
                {p.items.map((s) => (
                  <tr key={s.id} className="border-b border-sand">
                    <td className="py-2 pr-4"><Link className="text-emerald underline" to={`/admin/sources/${s.id}`}>{s.title}</Link></td>
                    <td className="pr-4">{s.category}</td><td className="pr-4">{STATUS_LABEL[s.approval_status] ?? s.approval_status}</td><td>{s.commercial_use}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Async>
      <h2 className="mt-10 text-2xl">Register a source</h2>
      <form className="mt-4 grid max-w-xl gap-3" onSubmit={(e) => { e.preventDefault(); create.mutate() }}>
        <TextField label="Slug (lowercase-with-dashes)" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
        <TextField label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <label className="text-sm font-medium">Category
          <select className="mt-1 block min-h-11 w-full rounded-md border border-sage bg-white px-3" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {['quran_text', 'quran_translation', 'tafsir', 'hadith_collection', 'dua', 'educational'].map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <TextField label="Language code" value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })} />
        {create.error && <FormError title={errText(create.error)!} />}
        <Button type="submit" disabled={create.isPending}>Register source</Button>
      </form>
    </>
  )
}

const PERMS = ['unknown', 'allowed', 'restricted', 'denied']
const FIELDS = ['commercial_use', 'storage_permission', 'indexing_permission', 'rag_permission'] as const

export function AdminSourceDetail() {
  const { id } = useParams()
  const qc = useQueryClient()
  const refresh = () => { void qc.invalidateQueries({ queryKey: ['admin-source', id] }); void qc.invalidateQueries({ queryKey: ['admin-sources'] }) }
  const src = useQuery({ queryKey: ['admin-source', id], queryFn: () => api<AdminSource>(`/admin/sources/${id}`, { auth: true }) })
  const ready = useQuery({ queryKey: ['admin-source', id, 'ready'], queryFn: () => api<Readiness>(`/admin/sources/${id}/readiness`, { auth: true }) })
  const reviews = useQuery({ queryKey: ['admin-source', id, 'reviews'], queryFn: () => api<Review[]>(`/admin/sources/${id}/reviews`, { auth: true }) })
  const [note, setNote] = useState('')
  const [rights, setRights] = useState<Record<string, string>>({})
  const act = useMutation({
    mutationFn: ({ path, method = 'POST', json }: { path: string; method?: string; json: unknown }) => api(`/admin/sources/${id}${path}`, { method, auth: true, json }),
    onSuccess: () => { refresh(); void qc.invalidateQueries({ queryKey: ['admin-source', id, 'ready'] }); void qc.invalidateQueries({ queryKey: ['admin-source', id, 'reviews'] }) },
  })
  return (
    <Async query={src}>
      {(s) => (
        <div className="space-y-8">
          <div>
            <Link to="/admin/sources" className="text-sm text-emerald underline">All sources</Link>
            <h2 className="mt-2 text-2xl">{s.title}</h2>
            <p className="text-sm">Status: <strong>{STATUS_LABEL[s.approval_status] ?? s.approval_status}</strong> · Licence verified: {s.license_verified_at ? new Date(s.license_verified_at).toLocaleDateString() : 'no'} · Content: {s.verification_status}</p>
          </div>
          {errText(act.error) && <FormError title={errText(act.error)!} />}

          <Card className="space-y-3">
            <h3 className="font-display text-xl">Rights and licence</h3>
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); act.mutate({ path: '/rights', method: 'PATCH', json: rights }) }}>
              <TextField label="Rights holder" defaultValue={s.rights_holder ?? ''} onChange={(e) => setRights({ ...rights, rights_holder: e.target.value })} />
              <TextField label="Licence name" defaultValue={s.license_name ?? ''} onChange={(e) => setRights({ ...rights, license_name: e.target.value })} />
              <TextField label="Licence URL" defaultValue={s.license_url ?? ''} onChange={(e) => setRights({ ...rights, license_url: e.target.value })} />
              <TextField label="Credit text to display" defaultValue={s.attribution_text ?? ''} onChange={(e) => setRights({ ...rights, attribution_text: e.target.value })} />
              {FIELDS.map((f) => (
                <label key={f} className="text-sm font-medium">{f.replace('_', ' ')}
                  <select className="mt-1 block min-h-11 w-full rounded-md border border-sage bg-white px-3" defaultValue={s[f]} onChange={(e) => setRights({ ...rights, [f]: e.target.value })}>
                    {PERMS.map((p) => <option key={p}>{p}</option>)}
                  </select>
                </label>
              ))}
              <div className="sm:col-span-2"><Button type="submit" disabled={act.isPending || Object.keys(rights).length === 0}>Save rights</Button></div>
            </form>
            <p className="text-xs">Changing rights on an approved source sends it back to review and clears the licence check.</p>
          </Card>

          <Card className="space-y-3">
            <h3 className="font-display text-xl">Review steps</h3>
            <TextField label="Note (what you checked)" value={note} onChange={(e) => setNote(e.target.value)} />
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" disabled={note.trim().length < 3 || act.isPending} onClick={() => act.mutate({ path: '/verify-licence', json: { note } })}>I verified the licence</Button>
              <Button variant="secondary" disabled={note.trim().length < 3 || act.isPending} onClick={() => act.mutate({ path: '/verify-content', json: { note } })}>I verified the content</Button>
            </div>
            <Async query={ready}>{(r) => r.ready ? <p className="text-sm font-medium text-emerald">Ready to approve.</p> : (
              <div className="text-sm"><p className="font-medium">Before approval:</p><ul className="list-disc pl-6">{r.missing.map((m) => <li key={m}>{m}</li>)}</ul></div>)}</Async>
            <div className="flex flex-wrap gap-2">
              {['candidate', 'pending_permission', 'restricted', 'under_review', 'approved', 'rejected', 'archived'].filter((x) => x !== s.approval_status).map((to) => (
                <Button key={to} variant={to === 'approved' ? 'primary' : 'secondary'} disabled={note.trim().length < 3 || act.isPending}
                  onClick={() => act.mutate({ path: '/status', json: { to_status: to, note } })}>→ {STATUS_LABEL[to]}</Button>
              ))}
            </div>
          </Card>

          <ImportCard sourceId={Number(id)} onDone={refresh} />

          <Card>
            <h3 className="font-display text-xl">History</h3>
            <Async query={reviews}>{(rs) => rs.length === 0 ? <p className="text-sm">No changes yet.</p> : (
              <ul className="mt-2 space-y-1 text-sm">{rs.map((r) => <li key={r.id}>{new Date(r.created_at).toLocaleString()} — {r.from_status} → {r.to_status}{r.note ? `: ${r.note}` : ''}</li>)}</ul>)}</Async>
          </Card>
        </div>
      )}
    </Async>
  )
}

const KIND_HELP: Record<string, string> = {
  surahs: 'JSON list: number, verse_count, name_arabic, name_english',
  quran_arabic: 'Lines: surah|verse|text',
  quran_translation: 'Lines: surah|verse|text (needs language)',
  tafsir: 'JSON lines: surah_number, verse_start, verse_end, language, text',
  hadith: 'JSON lines: hadith_number, texts… (needs collection slug and name)',
  duas: 'JSON lines: category_slug, category_name_english, title, arabic_text, reference_text…',
}

function ImportCard({ sourceId, onDone }: { sourceId: number; onDone: () => void }) {
  const check = useQuery({ queryKey: ['import-check', sourceId], queryFn: () => api<{ allowed: boolean; blockers: string[] }>(`/admin/sources/${sourceId}/imports/check`, { auth: true }) })
  const [kind, setKind] = useState('surahs')
  const [label, setLabel] = useState('')
  const [language, setLanguage] = useState('')
  const [slug, setSlug] = useState('')
  const [cname, setCname] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const upload = useMutation({
    mutationFn: () => {
      const p = new URLSearchParams({ kind, version_label: label, filename: file!.name })
      if (language) p.set('language', language)
      if (slug) p.set('collection_slug', slug)
      if (cname) p.set('collection_name', cname)
      return api<{ unchanged: boolean; counts: Record<string, number> }>(`/admin/sources/${sourceId}/imports?${p}`, { method: 'POST', auth: true, raw: file! })
    },
    onSuccess: onDone,
  })
  return (
    <Card className="space-y-3">
      <h3 className="font-display text-xl">Import a file</h3>
      <Async query={check}>{(c) => c.allowed ? <p className="text-sm text-emerald">Licence gate passed: this source may be imported.</p> : (
        <div className="text-sm"><p className="font-medium">Import is blocked:</p><ul className="list-disc pl-6">{c.blockers.map((b) => <li key={b}>{b}</li>)}</ul></div>)}</Async>
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); upload.mutate() }}>
        <label className="text-sm font-medium">File kind
          <select className="mt-1 block min-h-11 w-full rounded-md border border-sage bg-white px-3" value={kind} onChange={(e) => setKind(e.target.value)}>
            {Object.keys(KIND_HELP).map((k) => <option key={k}>{k}</option>)}
          </select>
        </label>
        <TextField label="Version label" hint="For example the date or release name" value={label} onChange={(e) => setLabel(e.target.value)} />
        <TextField label="Language code (translations)" value={language} onChange={(e) => setLanguage(e.target.value)} />
        <div />
        <TextField label="Collection slug (hadith)" value={slug} onChange={(e) => setSlug(e.target.value)} />
        <TextField label="Collection name (hadith)" value={cname} onChange={(e) => setCname(e.target.value)} />
        <div className="sm:col-span-2">
          <label className="text-sm font-medium" htmlFor="file">File</label>
          <input id="file" type="file" className="mt-1 block text-sm" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <p className="mt-1 text-xs">{KIND_HELP[kind]}. The whole file is checked first; if any line is wrong, nothing is imported.</p>
        </div>
        {upload.error && <div className="sm:col-span-2"><FormError title={errText(upload.error)!} /></div>}
        {upload.data && <p role="status" className="sm:col-span-2 text-sm text-emerald">{upload.data.unchanged ? 'This exact file was already imported; nothing changed.' : `Imported: ${JSON.stringify(upload.data.counts)}`}</p>}
        <div className="sm:col-span-2"><Button type="submit" disabled={!file || !label.trim() || upload.isPending || !check.data?.allowed}>Import</Button></div>
      </form>
    </Card>
  )
}

export function AdminUsers() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['admin-users'], queryFn: () => api<Page<User>>('/admin/users?limit=100', { auth: true }) })
  const role = useMutation({
    mutationFn: ({ id, r, grant }: { id: string; r: string; grant: boolean }) =>
      grant ? api(`/admin/users/${id}/roles`, { method: 'POST', auth: true, json: { role: r } }) : api(`/admin/users/${id}/roles/${r}`, { method: 'DELETE', auth: true }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['admin-users'] }),
  })
  return (
    <>
      {role.error && <FormError title={errText(role.error)!} />}
      <Async query={q}>
        {(p) => (
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Users</caption>
            <thead><tr className="border-b border-sand"><th className="py-2">Email</th><th>Roles</th><th>Editor</th></tr></thead>
            <tbody>
              {p.items.map((u) => (
                <tr key={u.id} className="border-b border-sand">
                  <td className="py-2">{u.email}</td><td>{u.roles.join(', ')}</td>
                  <td><Button variant="quiet" onClick={() => role.mutate({ id: u.id, r: 'editor', grant: !u.roles.includes('editor') })}>{u.roles.includes('editor') ? 'Remove editor' : 'Make editor'}</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Async>
    </>
  )
}

export function AdminAudit() {
  const q = useQuery({ queryKey: ['admin-audit'], queryFn: () => api<Page<AuditEvent>>('/admin/audit?limit=100', { auth: true }) })
  return (
    <Async query={q}>
      {(p) => p.items.length === 0 ? <p>No events yet.</p> : (
        <ul className="space-y-1 text-sm">{p.items.map((e) => <li key={e.id}>{new Date(e.created_at).toLocaleString()} — <strong>{e.action}</strong> {e.entity_type} {e.entity_id}</li>)}</ul>
      )}
    </Async>
  )
}

type AdminItem = { id: number; title: string; approval_status: string; question_count?: number; item_count?: number }

function ApproveList({ title, path, statusPath }: { title: string; path: string; statusPath: (id: number) => string }) {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: [path], queryFn: () => api<AdminItem[]>(path, { auth: true }) })
  const set = useMutation({
    mutationFn: ({ id, to }: { id: number; to: string }) => api(statusPath(id), { method: 'POST', auth: true, json: { to_status: to } }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: [path] }),
  })
  return (
    <section>
      <h2 className="text-2xl">{title}</h2>
      {set.error && <div className="mt-2"><FormError title={errText(set.error)!} /></div>}
      <Async query={q}>
        {(items) => items.length === 0 ? <p className="mt-2 text-sm">None yet. Create one below; it stays hidden until approved.</p> : (
          <ul className="mt-3 space-y-2">
            {items.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-sand bg-white px-4 py-2 text-sm">
                <span>{i.title} · {i.approval_status}</span>
                <span className="flex gap-2">
                  {i.approval_status !== 'approved' && <Button variant="secondary" onClick={() => set.mutate({ id: i.id, to: 'approved' })}>Approve</Button>}
                  {i.approval_status === 'approved' && <Button variant="secondary" onClick={() => set.mutate({ id: i.id, to: 'archived' })}>Archive</Button>}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Async>
    </section>
  )
}

export function AdminLearning() {
  return (
    <div className="space-y-10">
      <ApproveList title="Quizzes" path="/admin/quizzes" statusPath={(id) => `/admin/quizzes/${id}/status`} />
      <QuizBuilder />
      <ApproveList title="Learning paths" path="/admin/paths" statusPath={(id) => `/admin/paths/${id}/status`} />
      <PathBuilder />
    </div>
  )
}
