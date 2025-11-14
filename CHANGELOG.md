# Changelog

## [0.2.0] - 2024-11-14
- Consolidated the UI into the root `app/` App Router, migrating components, libs, Vitest config, and API proxies so `/inbox`, `/capsules`, `/graph`, `/chat`, and `/capsules/[id]` are served from a single Next.js tree.
- Aligned `apps/engine` with `infra/sql/0004_update_vector_dimension.sql`, introduced deterministic chunk metadata + chunk IDs, and enforced PII guardrails before storing capsules.
- Added SSE health coverage, a privacy scan, and a CI workflow that runs lint/typecheck, Vitest, Pytest, schema alignment, and guardrail checks while documenting the release in `docs/v0.2-upgrade-notes.md`.
