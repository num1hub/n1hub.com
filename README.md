# N1Hub.com

**AI-native knowledge system — _Anything → Capsules → Graph → Chat_.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?logo=node.js&logoColor=fff)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs)](https://nextjs.org/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-%2B%20pgvector-336791?logo=postgresql&logoColor=fff)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7.x-dc382d?logo=redis&logoColor=fff)](https://redis.io/)

---

## Overview

**N1Hub.com** is a full-stack, spec-aligned reference implementation of a CapsuleOS. The product accepts almost any source artifact (**Anything**), normalises and segments the content into validated **Capsules**, links capsules into a semantic **Graph**, and serves grounded **Chat** responses with strict citations through a hybrid RAG stack.

Key ingredients:

- **DeepMine pipeline** – normalisation, summarisation, validation, embeddings, and linking handled in `apps/engine/app/pipeline.py`.
- **Knowledge Capsules** – schema enforced by `N1Hub.com_V0.1_Capsule_EN.approved.v1.2.0.json` and the validator suite.
- **Hybrid retrieval** – pgvector + lexical search orchestrated in `apps/engine/app/rag.py`.
- **Next.js interface** – App Router UI in `app/` with API proxy routes under `app/api/*`.

---

## Architecture at a glance

```mermaid
flowchart LR
    subgraph Browser["User (Browser)"]
      UI[Next.js Interface\napp/]
    end

    subgraph Frontend["Frontend"]
      APIProxy["App Router API routes\n/app/api/*"]
    end

    subgraph Engine["FastAPI Engine (apps/engine)"]
      Ingest["pipeline.py\nDeepMine ingestion"]
      RAG["rag.py\nsemantic + lexical"]
      Vec["vectorizer.py\nembeddings"]
      Events["events.py\nSSE"]
      Obs["observability.py\nhealth/metrics"]
      Store["store_pg.py\nPostgres + pgvector"]
    end

    subgraph Data["Data Services"]
      PG[(Postgres + pgvector)]
      Redis[(Redis)]
    end

    UI -- fetch --> APIProxy
    APIProxy -- HTTP --> Engine
    Engine <---> PG
    Engine <---> Redis
    UI -. SSE .-> Events
```

---

## Repository layout

```text
n1hub.com/
├─ app/                      # Next.js App Router interface and API proxy routes
├─ apps/
│  └─ engine/                # FastAPI backend (pipeline, RAG, validators, SSE, observability)
├─ components/               # Shared React UI components
├─ hooks/                    # Reusable React hooks
├─ lib/                      # Frontend utilities (engine proxy, fetch helpers, etc.)
├─ __tests__/                # Vitest suites for the frontend
├─ infra/
│  ├─ docker-compose.yml     # Local Postgres + Redis
│  └─ sql/                   # Forward-only SQL migrations
├─ scripts/                  # Dev helpers, migrations, env validation
├─ tools/                    # Capsule/spec alignment and privacy checks
├─ docs/                     # Architecture, env, deployment, readiness docs
└─ config/
   ├─ .env.example           # Local development template
   └─ .env.production.example# Production deployment template
```

---

## Quickstart (local dev)

The steps below produce a working stack on macOS/Linux or Windows 10+. Commands are copy/paste ready.

### 1. Prerequisites

- Git
- Python 3.11+
- Node.js 20+ and pnpm (`corepack enable` enables pnpm on Node 20)
- Docker Desktop (for Postgres + Redis)
- PostgreSQL client (`psql`) on your host machine

Verify versions:

```bash
git --version
python3 --version
node --version
pnpm --version
docker --version
psql --version
```

### 2. Clone & configure

```bash
git clone https://github.com/num1hub/N1Hub.com.git
cd N1Hub.com

cp config/.env.example config/.env
# Optional production template
cp config/.env.production.example config/.env.production
```

Update `config/.env` with any local overrides (DSNs, optional LLM credentials). All variable definitions are documented in [`docs/env-reference.md`](docs/env-reference.md).

### 3. Start data services

```bash
cd infra
docker compose up -d
cd ..
```

This launches Postgres (port 5432) and Redis (port 6379).

### 4. Apply migrations

macOS/Linux:

```bash
./scripts/migrate.sh --database-url postgresql://postgres:postgres@localhost:5432/n1hub
./scripts/verify_migrations.sh --database-url postgresql://postgres:postgres@localhost:5432/n1hub
```

Windows (PowerShell):

```powershell
./scripts/migrate.ps1 -DatabaseUrl "postgresql://postgres:postgres@localhost:5432/n1hub"
./scripts/verify_migrations.ps1 -DatabaseUrl "postgresql://postgres:postgres@localhost:5432/n1hub"
```

### 5. Start the FastAPI engine

macOS/Linux:

```bash
python3 -m venv apps/engine/.venv
source apps/engine/.venv/bin/activate
pip install -e "apps/engine[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/engine
```

Windows (PowerShell):

```powershell
python -m venv apps\engine\.venv
./apps/engine/.venv/Scripts/Activate.ps1
pip install -e "apps/engine[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/engine
```

> Tip: `pnpm dev:stack:unix` or `pnpm dev:stack:win` bootstraps the virtualenv, installs engine deps, brings up Docker services, and runs Uvicorn with autoreload.

Engine health endpoints: [`/healthz`](http://127.0.0.1:8000/healthz), [`/readyz`](http://127.0.0.1:8000/readyz), [`/livez`](http://127.0.0.1:8000/livez). API docs: [`/docs`](http://127.0.0.1:8000/docs).

### 6. Start the Next.js interface

In a new terminal at repo root:

```bash
pnpm install
pnpm dev
```

Visit [http://localhost:3000](http://localhost:3000). If the browser cannot reach the engine, set:

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
export NEXT_PUBLIC_SSE_URL=http://127.0.0.1:8000/events/stream
export ENGINE_BASE_URL=http://127.0.0.1:8000
```

On Windows PowerShell:

```powershell
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
$env:NEXT_PUBLIC_SSE_URL="http://127.0.0.1:8000/events/stream"
$env:ENGINE_BASE_URL="http://127.0.0.1:8000"
```

### 7. Smoke test

1. Upload the sample documents from `/examples/demo-dataset/` via the UI.
2. Watch ingestion progress in **Inbox** (`/inbox`).
3. Open **Capsules** (`/capsules`) to confirm the new capsule.
4. Ask a question in **Chat** (`/chat`) and confirm citations reference stored capsules.

---

## Configuration

| Variable | Purpose | Default (config/.env.example) |
| --- | --- | --- |
| `STORE_BACKEND` | Storage implementation (`postgres` recommended) | `postgres` |
| `N1HUB_POSTGRES_DSN` | Engine Postgres DSN | `postgresql://postgres:postgres@localhost:5432/n1hub` |
| `N1HUB_REDIS_URL` | Redis connection string (optional) | `redis://localhost:6379/0` |
| `N1HUB_LLM_PROVIDER` | LLM provider (`anthropic` or `openai`) | `anthropic` |
| `N1HUB_LLM_API_KEY` | LLM API key (optional) | _empty_ |
| `N1HUB_LLM_MODEL` | LLM model name | `claude-3-haiku-20240307` |
| `N1HUB_EMBEDDING_MODEL` | Embedding model identifier | `all-MiniLM-L6-v2` |
| `N1HUB_EMBEDDING_DIMENSION` | Expected embedding vector dimension | `384` |
| `NEXT_PUBLIC_API_URL` | Engine base URL for the browser | `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_SSE_URL` | SSE stream URL | `http://127.0.0.1:8000/events/stream` |
| `ENGINE_BASE_URL` | Engine URL for Next.js server-side routes | `http://127.0.0.1:8000` |

The complete matrix (including optional rate limits and retention controls) lives in [`docs/env-reference.md`](docs/env-reference.md). Validate your environment with:

```bash
python scripts/validate_env.py --target backend --env-file config/.env
python scripts/validate_env.py --target frontend --env-file config/.env
```

---

## Tests & quality

| Command | Purpose |
| --- | --- |
| `pnpm lint` | ESLint flat config (Next.js + Vitest globals) |
| `pnpm typecheck` | TypeScript project references for the frontend |
| `pnpm test:ui` | Vitest unit/e2e suites under `__tests__/` |
| `pnpm test:engine` | Pytest unit suites (`-m "not integration"`) |
| `pnpm test:engine:integration` | Opt-in integration tests (require Postgres/Redis + migrations) |
| `./scripts/verify_migrations.sh` | Sanity-check database schema (macOS/Linux) |
| `python tools/validate_capsule_alignment.py` | Ensure repo stays aligned with the capsule spec |
| `python tools/privacy_scan.py` | Guard against PII in sample capsules |

CI mirrors these commands in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Deployment (budget-friendly v0.1 path)

Recommended split:

- **Frontend** → Vercel (Next.js App Router). Build command `pnpm build`, output `.next`.
- **Backend** → Railway or Render (FastAPI + Postgres + optional Redis). Use `railway.toml` or `render.yaml` as a starting point.
- **Data services** → Managed Postgres with pgvector + optional Redis cache.

Essential production variables:

```text
STORE_BACKEND=postgres
N1HUB_POSTGRES_DSN=postgresql://...  # Provided by Railway/Render
N1HUB_REDIS_URL=redis://...          # Optional but recommended
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_SSE_URL=https://api.your-domain.com/events/stream
ENGINE_BASE_URL=https://api.your-domain.com
```

Run migrations before releasing (`scripts/migrate.*`), validate environments (`scripts/validate_env.py`), and confirm health endpoints return `200`.

Detailed deployment instructions live in [`docs/deployment.md`](docs/deployment.md).

---

## Additional documentation

- [`docs/N1Hub-v0.1-architecture.md`](docs/N1Hub-v0.1-architecture.md) – end-to-end system architecture.
- [`docs/user-guide.md`](docs/user-guide.md) – UI walkthrough for ingestion, capsules, graph, and chat.
- [`docs/production-checklist.md`](docs/production-checklist.md) – final checks before go-live.
- [`docs/v0.1-final-polish-plan.md`](docs/v0.1-final-polish-plan.md) – readiness status and follow-up tasks.

---

## Troubleshooting

- **UI cannot reach engine** – confirm `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SSE_URL`, and `ENGINE_BASE_URL` match the running backend.
- **Migrations fail** – ensure Docker services are running, `psql` is installed, and the DSN matches the container credentials.
- **SSE not streaming** – verify proxies allow `text/event-stream` and disable buffering.
- **429 Too Many Requests** – respect `Retry-After`; reduce concurrent ingestion jobs.
- **Vector dimension mismatch** – ensure migration `0004_update_vector_dimension.sql` has run and the embedding model outputs 384-d vectors.

---

## Contributing

We welcome issues and pull requests. Before opening a PR:

1. Run the same checks that CI runs (`pnpm lint`, `pnpm typecheck`, `pnpm test:ui`, `pnpm test:engine`).
2. Update documentation when behaviour or configuration changes.
3. Keep `config/.env.example` and `docs/env-reference.md` in sync with any new environment variables.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guidelines.

---

## Security & privacy

- Never commit secrets or real `.env` files.
- Redact sensitive data from logs, screenshots, and sample capsules.
- Use demo data during local development and testing.

If you spot a security issue, open a short issue describing the concern and request a private follow-up channel.

---

## License

TBD. If you intend to redistribute or open-source the project, add an appropriate license file (for example MIT) and update this section accordingly.

---

## Support

- Issues: https://github.com/num1hub/N1Hub.com/issues
- Engine health checks: `/healthz`, `/readyz`, `/livez`
- Built as a pragmatic reference for the “Anything → Capsules → Graph → Chat” workflow.
