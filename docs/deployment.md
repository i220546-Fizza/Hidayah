# Deployment guide (nothing has been deployed)

Do not deploy until you approve. This lists what is needed so you can decide.

## Before any public launch
1. Licence decisions: at least one approved Arabic Quran text and one English translation. Until then the site shows honest empty states. See `docs/source-register.md`.
2. Lawyer review of Privacy and Terms (currently marked draft on the site).
3. A chosen embedding provider if you want semantic search (keyword search works without it).
4. Test the mobile app on real phones.

## Pieces you would need (these can cost money; ask me first)
- PostgreSQL 16 with pgvector (managed database or your own server).
- A host for the FastAPI backend (one process to start; multiple processes need a shared rate limiter such as Redis).
- Static hosting for the website (`frontend`, `npm run build`, serve `dist/`).
- A domain name and HTTPS. In production the refresh cookie becomes `Secure` automatically.
- An Anthropic API key for answers (set as `ANTHROPIC_API_KEY` in the host's secret store, never in git).
- An email service (SMTP) for verification and password-reset mail: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM`, `PUBLIC_SITE_URL`. Without it no mail is sent. Optionally error monitoring.
- For store apps: Google Play and Apple developer accounts, Expo EAS builds, real bundle identifiers.

## Required settings (environment variables)
`ENV=production`, `DATABASE_URL`, `SECRET_KEY` (32+ random characters; the app refuses to start otherwise), `ALLOWED_ORIGINS` (your website address), `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (optional), and `VITE_API_BASE_URL` when building the website.

## Steps once approved
1. Create the database, enable pgvector, run `alembic upgrade head` from `backend/`.
2. Create the first administrator: `python -m app.cli create-admin --email you@example.com` (password typed hidden).
3. Register sources in the admin dashboard, verify licences, import files, approve.
4. Build and publish the website; point it at the API.
5. Back up the database and test a restore.
