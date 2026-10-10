# Architecture

Web, mobile and admin clients talk to one FastAPI backend over versioned HTTPS JSON
(`/api/v1`). The backend is a modular monolith: `api` (routes) calls `services` (business
logic), which call `repositories` and `models` (PostgreSQL). `rag`, `ingestion` and `providers`
(LLM and embedding adapters) are separate modules. A background worker handles ingestion and
re-indexing. PostgreSQL holds relational data, vectors (pgvector) and full-text indexes.

Currently built: the web app's design foundation and landing page only.
Full detail is added as each phase is implemented.
