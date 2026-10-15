# Feature checklist

Statuses: Not Started, In Progress, Implemented, Tested, Blocked.
"Tested" means automated tests actually ran and passed.

## Phase 2: design foundation

| Item | Status | Notes |
|---|---|---|
| Web design tokens (CSS variables, Tailwind theme) | Tested | Contrast checked, see below |
| Mobile design tokens | Implemented | `mobile/src/theme/tokens.ts`; app not created yet |
| Fonts (Playfair, Inter, Amiri, Noto Naskh, Noto Nastaliq) | Implemented | Self-hosted via npm; visual check on a real device pending |
| Logo and emblem | Implemented | Arabic spelling needs human verification before launch |
| Reusable components (Button, Card, Container, EmptyState) | Tested | |
| Responsive navigation | Tested | Menu toggle test; real-device check pending |
| Landing page | Tested | Verse and dua areas are honest empty states until verified data exists |

## Phase 3: backend and database

| Item | Status | Notes |
|---|---|---|
| FastAPI app, config, JSON logging, CORS | Tested | |
| /health and /ready (database + pgvector) | Tested | Verified over real HTTP, including DB stopped (503) |
| 42-table schema, Alembic migration 0001 | Tested | Up, down and up again; no drift between models and migration |
| Licence rule enforced by the database | Tested | Each rejection checked against the intended constraint |
| pgvector (vector search, HNSW index) | Tested | pgvector 0.6.0 in the sandbox; Docker image will be newer |
| Full-text search column | Tested | |
| Persistence across a PostgreSQL restart | Tested | Real server restart, data intact |
| docker-compose database | Implemented | NOT run in the sandbox (no Docker engine); you ran the same image earlier |
| Backend running on Windows | Not Tested | Tested on Linux only |

## Phase 4: accounts and authorization

| Item | Status | Notes |
|---|---|---|
| Register, login, refresh, logout, logout-all | Tested | 126 backend tests plus real HTTP check, web cookie flow included |
| Password hashing (Argon2id) and token design | Tested | See `docs/security.md` |
| Refresh rotation and reuse detection | Tested | Replayed token revokes all sessions |
| Roles checked on the server | Tested | User gets 403 on admin routes; last-admin protected |
| Profile, preferences, password change | Tested | |
| Bookmarks (own data only) | Tested | Other users' bookmarks are invisible |
| Data export and account deletion | Tested | |
| Login/register pages, header state, session handling | Tested | 27 frontend tests; not yet checked in a real browser |
| Login survives a server restart | Tested | Real restart; data is in PostgreSQL |
| Rate limiting | Implemented | In memory, one process only; needs Redis or a gateway to scale out |
| Email verification | Blocked | Needs an email service and credentials from you |
| Password reset by email | Blocked | Same reason |
| Mobile secure token storage | Not Started | Phase 9 |
| Running on Windows | Tested | Backend, migrations, 126 tests, health check run on your Windows PC with Docker Desktop |
| Local database on host port 5433 | Tested | Container healthy, `check-db` OK, pgvector 0.8.1, migration 0001; the 126 tests took 17 minutes there (30 s in the sandbox): cause not yet investigated |

## Phases 5 to 9: sources, content, assistant, learning, web, mobile

"Tested" = automated tests passed in the build sandbox. "Browser-checked" = run in Chromium against the real backend with a throwaway database of obvious placeholder text.

| Item | Status | Notes |
|---|---|---|
| Source register and licence review | Tested | 16 API tests; statuses, rights fields, review history, audit log |
| Licence gate (nothing unapproved is shown or indexed) | Tested | DB constraint + service checks + content/ask/quiz tests |
| Import pipeline (6 file kinds, API + CLI) | Tested | 23 tests: gate, all-or-nothing, text kept exactly, same-file idempotency |
| Public Quran/tafsir/hadith/dua/search APIs | Tested | 8 tests; hidden sources never appear |
| Ask pipeline (retrieval, guard rails, citations, history, feedback, rate limit) | Tested with a stand-in model | 17 tests. NOT tested against live Claude: needs `ANTHROPIC_API_KEY` |
| Vector search | Tested with fake embeddings only | No embedding provider chosen yet; keyword search works without one |
| Learning paths, quizzes, daily verse, reading progress, admin stats | Tested | 12 tests |
| Web pages (all of the above plus account and admin) | Tested + Browser-checked | 41 web tests; 23 browser checks incl. 375px width |
| Mobile app | Bundled only | Type check, 9 client tests, Android+iOS Metro bundle. Never run on a phone |
| Admin: create quizzes and paths | Tested + Browser-checked | Forms in the admin Learning tab; quiz can't be approved without approved-source explanations |
| Urdu | Partly done | Reader has an English/Urdu translation switch with Urdu font and right-to-left text; works as soon as an Urdu source is approved. The Urdu SOURCES are not obtained (licensing) and the interface itself is English only. Ask answers are English only |
| Quran, hadith, dua CONTENT | Blocked | Nothing imported. Needs licence decisions, see `docs/source-register.md` |
| Email verification, password reset | Tested + Browser-checked | One-time hashed links, 2 h expiry, reset signs out all devices, same reply for unknown emails. Nothing is sent until you configure `SMTP_HOST`; in development the link is logged. NOT tested with a real mail server |
| Deployment | Not Started | Needs your approval; see `docs/deployment.md` |

## Contrast check (WCAG, measured)

Normal text needs 4.5:1. Charcoal on ivory 11.8, ivory on emerald 11.2, emerald on white 12.2,
gold on emerald 5.2. Gold on ivory is 2.2, so gold is never used for text on ivory.
Bronze on ivory is 4.49, used only for the logo's Arabic wordmark.
