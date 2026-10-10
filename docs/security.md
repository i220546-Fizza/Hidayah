# Security design (Phase 4)

Written in plain language so you can learn from it. Update it whenever auth changes.

## Passwords
Hashed with **Argon2id** (slow on purpose, so stolen hashes are hard to crack). We never store or log
the password. Login errors are generic ("Incorrect email or password") and a dummy hash is checked for
unknown emails so response time does not reveal which emails exist.

## Tokens
- **Access token**: JWT, 15 minutes, HS256 with pinned algorithm, issuer checked. Each request also
  checks its session row in the database, so logging out takes effect immediately.
- **Refresh token**: random value; only its SHA-256 hash is stored. Each use **rotates** it. If an
  already-used token is replayed (a sign of theft), all of that user's sessions are revoked.
- **Web**: refresh token is an HttpOnly, SameSite=Strict cookie scoped to `/api/v1/auth` (Secure outside
  development). The access token lives only in memory, never in localStorage. State-changing auth calls
  require the `X-Hidayah-Client: web` header, a CSRF defence.
- **Mobile**: refresh token comes in the JSON body; Phase 9 will keep it in the OS secure store.

## Authorization
Roles are loaded and checked on the server on every request (`require_role`, `require_admin`). The
frontend hiding a button is only convenience. The last admin cannot be removed or demoted.

## Rate limiting (known limitation)
Login and registration are limited per client in memory. This resets on restart and is not shared across
several server copies. Before scaling out, move it to Redis or the gateway. Behind a reverse proxy, the
client IP must come from a trusted forwarded header, or all users share one limit.

## Secrets
`SECRET_KEY` and other secrets come from environment variables only. In production the app refuses to
start with the development default or a short key. The admin CLI reads passwords with a hidden prompt.

## Privacy
Users can export their data and delete their account (password required). Audit events record sensitive
actions such as role changes.

## Not built yet
Email verification and password reset (need an email provider), two-factor login, and mobile secure
storage.
