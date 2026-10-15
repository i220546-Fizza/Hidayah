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

## Review of Phases 5 to 9 (assistant, content, admin, mobile)

Checked by reading the code and by tests unless marked otherwise.

**Held up**
- Every public and assistant query goes through an approved source, and the assistant also needs `rag_permission`. Tests prove that unapproved, under-review and later-revoked content disappears (including from saved answers).
- Admin routes (`/admin/*`) all use `require_admin`; learner routes that change data use the signed-in user and never accept a user id from the request.
- Conversations and feedback are owner-only (404 for other people's).
- The assistant cannot invent a citation: citations are rows from our database; answers that name unknown evidence, are malformed, or contain Arabic script are discarded. Evidence text is escaped before it enters the prompt.
- Quiz answers are never sent to the learner before submitting; scoring is on the server.
- Import is all-or-nothing, byte-exact, and refuses unless the licence gate passes.
- The Anthropic key is read only from the environment; no key is in code, tests or docs.
- Mobile: refresh token in Keychain/Keystore (SecureStore), access token in memory only.

**Known limits (not fixed)**
- Rate limiting is in memory and per process (see Phase 4). The ask limit has the same limit. Public search and content endpoints are not rate limited; search uses a scan (`ILIKE`) that will need an index or a proper search backend at scale.
- The admin file upload reads the whole body into memory before the 50 MB check. Fine for a trusted admin; put a body-size limit on the reverse proxy.
- Questions are sent to Anthropic with retrieved passages; the privacy page says so but is draft text pending legal review.
- Chrome-level checks (CSP headers, HTTPS, secure cookies in production) need a real deployment to verify.
- No third-party penetration test or dependency audit has been done (`npm audit` reports advisories in Expo's tree; not triaged).
