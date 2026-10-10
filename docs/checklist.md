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

## Everything else

| Area | Status |
|---|---|
| Authentication and accounts | Not Started |
| Quran, translation, tafsir | Not Started (licensing review first) |
| Hadith and gradings | Not Started (licensing review first) |
| Duas | Not Started |
| RAG assistant | Not Started |
| Daily Companion, quizzes, learning paths | Not Started |
| Admin dashboard | Not Started |
| Mobile app | Not Started |
| Deployment | Not Started (needs your approval) |

## Contrast check (WCAG, measured)

Normal text needs 4.5:1. Charcoal on ivory 11.8, ivory on emerald 11.2, emerald on white 12.2,
gold on emerald 5.2. Gold on ivory is 2.2, so gold is never used for text on ivory.
Bronze on ivory is 4.49, used only for the logo's Arabic wordmark.
