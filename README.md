# Hidayah (هداية)

A Path to Knowledge, Faith & Guidance.

Hidayah is an Islamic learning platform: a website, an Android and iOS app, and one shared
backend. The goal is source-grounded learning from the Quran, tafsir, hadith and duas, with
every claim traceable to an approved source.

> **Status:** early development. Built so far: the web design foundation and landing page
> (Phase 2), and the backend skeleton with the database schema (Phase 3). See `docs/checklist.md` for what is and is not done.

## Structure

| Folder | Purpose |
|---|---|
| `frontend/` | Web app: React, TypeScript, Vite, Tailwind |
| `mobile/` | Android and iOS app: React Native with Expo (tokens only so far) |
| `backend/` | FastAPI API, PostgreSQL schema and migrations (RAG logic not started) |
| `data/` | Dataset provenance notes. No religious text is committed yet |
| `docs/` | Architecture, source policy, checklist |

## Prerequisites

Node 22+, npm 10+, Python 3.13, Git, Docker Desktop.

## Run the website

From the `frontend` folder, in PowerShell or any terminal:

```bash
npm install
npm run dev        # opens at http://localhost:5173
```

## Run the backend

PowerShell commands, in order. Start Docker Desktop first and wait until it says the engine is running.

```powershell
# 1. From the project root: create your private settings file (it is git-ignored)
Copy-Item .env.example .env

# 2. Is Docker's Linux engine up? This must print a version, not an error.
docker info --format "{{.ServerVersion}}"

# 3. Start the database. It listens on host port 5433 (container port stays 5432),
#    so it never collides with another PostgreSQL already using 5432.
docker compose up -d db
docker compose ps        # wait until STATUS says (healthy)
```

Then, in the `backend` folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m app.cli check-db       # shows user/port/database (never the password) and whether it connects
alembic upgrade head
alembic current                  # should print 0001 (head)
uvicorn app.main:app --reload    # http://localhost:8000/health and /ready, docs at /docs
```

The backend reads the root `.env` automatically, so you do not need to set `$env:DATABASE_URL`.
You can also run Alembic from the project root: `alembic -c backend/alembic.ini upgrade head`.

For sign-in on a real server set a long random `SECRET_KEY` in `.env`. Create the first admin
(register on the website first; the password is asked privately, never typed into chat):

```powershell
python -m app.cli create-admin --email you@example.com
```

Test the backend (needs the database running; it creates and drops a separate `hidayah_test`
database, so it needs the `TEST_DATABASE_URL` from `.env`):

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://hidayah:change-me@localhost:5433/hidayah_test"
python -m pytest -q
```

**Faster tests (optional).** On some Windows/Docker setups the first test takes minutes because the
disk is slow for many small writes. A throwaway in-memory test database avoids that and never touches your
real data:

```powershell
docker compose --profile test up -d db-test
$env:TEST_DATABASE_URL = "postgresql+psycopg://hidayah:change-me@localhost:5434/hidayah_test"
python -m pytest -q
docker compose --profile test stop db-test    # when you are done
```

### Database troubleshooting

| Symptom | Cause and fix |
|---|---|
| `failed to connect to the docker API` | Docker Desktop's Linux engine is not running. Open Docker Desktop and wait for "Engine running". |
| Container stuck in `Created`, port error | The host port is taken. Find who: `Get-NetTCPConnection -LocalPort 5433 -State Listen`. Pick another port in `.env` (`HIDAYAH_DB_PORT`) and the same port in `DATABASE_URL`, then `docker compose up -d db`. |
| `role "hidayah" does not exist` | Another PostgreSQL answers on that port, not the Hidayah container. Check the port in `DATABASE_URL` matches `HIDAYAH_DB_PORT`. |
| `password authentication failed` | The Docker volume remembers the password it was first created with. Changing `POSTGRES_PASSWORD` later does nothing. Use the original password. Do not delete the volume to "fix" it unless you accept losing the data. |

## What the app does now

- Website pages: Quran, Hadith, Duas, Search, Ask, Learning and quizzes, Sources and credits, Account, and an admin dashboard at `/admin` (create an administrator with `python -m app.cli create-admin --email you@example.com` from `backend/`).
- Every page shows honest empty states until a source is approved. To see content you must register a source in the admin dashboard, verify its licence, import a file, and approve it. Import only text you are permitted to use.
- The Ask page needs `ANTHROPIC_API_KEY` in your `.env` (the key stays on your computer). Without it the page says the assistant is not switched on.
- Phone app: see `mobile/README.md`.

## Test and build the website

```bash
npm test           # unit tests (Vitest)
npm run lint
npm run build      # type-check + production build into dist/
```

## Troubleshooting

- **`npm install` fails:** check your Node version with `node --version` (needs 22+).
- **Fonts look wrong:** fonts are installed from npm, so run `npm install` again.
- **Port 5173 in use:** Vite will offer the next free port; use the address it prints.

## Important

Religious texts are never invented or generated by this project. Content is added only after
its source, edition and license have been verified (see `docs/source-policy.md`).
