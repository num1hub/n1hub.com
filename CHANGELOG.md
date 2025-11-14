# Changelog

# [Unreleased]
- Added tracked environment templates under `config/` and taught the capsule alignment validator to require them.
- Refreshed the README with accurate repository layout, Quickstart, testing commands, and deployment guidance.
- Updated migration helpers to auto-discover forward SQL files and verify the `vector(384)` embedding column.
- Switched CI and documentation to use the `pnpm test:engine` / `pnpm test:ui` workflows and aligned historical docs with the root `app/` interface.

## [0.2.0] - 2024-11-14
- Consolidated the UI into the root `app/` App Router, migrating components, libs, Vitest config, and API proxies so `/inbox`, `/capsules`, `/graph`, `/chat`, and `/capsules/[id]` are served from a single Next.js tree.
- Aligned `apps/engine` with `infra/sql/0004_update_vector_dimension.sql`, introduced deterministic chunk metadata + chunk IDs, and enforced PII guardrails before storing capsules.
- Added SSE health coverage, a privacy scan, and a CI workflow that runs lint/typecheck, Vitest, Pytest, schema alignment, and guardrail checks while documenting the release in `docs/v0.2-upgrade-notes.md`.
