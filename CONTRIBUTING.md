Below is a **production‑ready `CONTRIBUTING.md`** tailored to the current repository layout, scripts, and environment flow. It aligns with the latest `README`, the existing contributing draft, and the project‑structure snapshot so that all paths and commands are copy‑paste runnable.

> Drop this file at the repo root as `CONTRIBUTING.md`. For a product overview (not the contribution process), see the main [README](./README.md). 

---

````markdown
# Contributing to N1Hub.com

Thank you for considering a contribution to **N1Hub.com** — an AI‑native knowledge system for the **“Anything → Capsules → Graph → Chat”** workflow. This document covers **how to contribute** to this repository: setting up a contributor dev environment, understanding the repo layout, running the same checks CI runs, and landing high‑quality Pull Requests. For an overview of what the product does, see the root [README](./README.md). :contentReference[oaicite:2]{index=2}

---

## 1) Code of Conduct

We foster a respectful, inclusive environment:
- Be kind and constructive.
- Assume good intent.
- Keep feedback focused on code and behavior, not people.

Participation in this project implies adherence to GitHub Community Guidelines.

---

## 2) Repository Layout (Contributor View)

N1Hub.com is a **Node workspaces** monorepo with a Python FastAPI backend and a Next.js frontend. The paths below are the canonical locations for the modules you’ll touch most. :contentReference[oaicite:3]{index=3}

- **Backend (engine)** — `apps/engine/`  
  Core modules:  
  `app/pipeline.py` (DeepMine ingestion), `app/rag.py` (retrieval/answering),  
  `app/vectorizer.py` (semantic embeddings), `app/validators/capsule_validator.py` (capsule contract),  
  `app/store_pg.py` (Postgres/pgvector I/O), `app/observability.py` (health/quality), tests in `apps/engine/tests/`. :contentReference[oaicite:4]{index=4}
- **Interface (primary frontend)** — `app/`  
  Next.js App Router (chat, capsules, graph, inbox), API proxy routes under `app/api/*`, components in `components/`, state and helpers in `lib/`, tests in `**tests**/`. :contentReference[oaicite:5]{index=5}
- **Root UI & shared kit** — `app/`, `components/` (shadcn/ui). :contentReference[oaicite:6]{index=6}
- **Infra** — `infra/docker-compose.yml` and SQL migrations under `infra/sql/0001…0004_*.sql`. :contentReference[oaicite:7]{index=7}
- **Docs** — `docs/` (architecture, API, env reference, deployment, examples). :contentReference[oaicite:8]{index=8}
- **Scripts & Tools** — `scripts/` (dev/migrate/verify), `tools/validate_capsule_alignment.py`. :contentReference[oaicite:9]{index=9}
- **CI & Templates** — `.github/workflows/ci.yml`, issue/PR templates in `.github/`. :contentReference[oaicite:10]{index=10}

---

## 3) Prerequisites

Install:
- **Git**
- **Python** 3.11+
- **Node.js** 20+ (18.17+ also works)
- **npm** (bundled with Node)
- **Docker Desktop** (for local Postgres + Redis)

These versions and the local‑dev expectations match the project’s README quickstart. :contentReference[oaicite:11]{index=11}

---

## 4) Dev Environment (Contributor Setup)

This flow mirrors the project’s documented quickstart to reduce “works on my machine” drift. :contentReference[oaicite:12]{index=12}

### 4.1 Clone & environment
```bash
git clone https://github.com/num1hub/n1hub.com.git
cd n1hub.com

mkdir -p config
cp config/.env.example config/.env
````

Edit `config/.env` for your machine (DB/Redis DSNs, optional LLM provider/key). See `docs/env-reference.md` for the full list. 

### 4.2 Start services (Postgres + Redis)

```bash
cd infra
docker compose up -d
cd ..
```

This uses `infra/docker-compose.yml`. 

### 4.3 Run database migrations

```bash
# macOS/Linux
./scripts/migrate.sh
./scripts/verify_migrations.sh   # optional but recommended

# Windows (PowerShell)
.\scripts\migrate.ps1
.\scripts\verify_migrations.ps1  # optional but recommended
```

Migration files live in `infra/sql/`. 

### 4.4 Start the backend (FastAPI engine)

```bash
cd apps/engine
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health/docs: `http://127.0.0.1:8000/healthz` and `http://127.0.0.1:8000/docs`. 

### 4.5 Start the frontend (interface)

```bash
# repo root in a new terminal
npm install
npm run dev:interface
```

Open `http://localhost:3000`. If the UI can’t reach the engine, set:

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
export NEXT_PUBLIC_SSE_URL=http://127.0.0.1:8000/events/stream
```

(You can also put these in `.env.local`.) 

### 4.6 One‑shot helper scripts (optional)

```bash
# Windows
.\scripts\dev-win.ps1
# macOS/Linux
./scripts/dev.sh
```

These bring up Docker services and start the interface; run the engine separately (step 4.4). 

---

## 5) Tests & Quality Gates

Run locally what CI will run:

```bash
# from repo root
npm run test:all
```

Or split by area:

```bash
# Backend (pytest)
npm run test:engine
# or
cd apps/engine && pytest

# Frontend (Vitest)
npm run test:interface
```

Commands and structure match the README and current test layout.

### Lint & typecheck (frontend)

```bash
npm run lint:interface
npm run typecheck
```

These are the checks CI expects for the interface. 

### Additional validations used by CI

* **Migration verification** — `scripts/verify_migrations.sh` / `.ps1`
* **Env validation** — `scripts/validate_env.py`
* **Capsule spec alignment** — `tools/validate_capsule_alignment.py`
  Run these locally when you touch schema, env, or capsule structure to avoid CI surprises. 

---

## 6) Database & Migrations

All schema changes must land as **new** SQL files under `infra/sql/` (use idempotent SQL where practical, e.g., `IF NOT EXISTS`). Typical flow:

1. create `infra/sql/000X_descriptive_name.sql`;
2. apply with `scripts/migrate.*`;
3. verify with `scripts/verify_migrations.*`;
4. commit together with the related code. 

> Never rewrite existing numbered migrations on `main`; always add a new one.

---

## 7) Coding Guidelines

### 7.1 Backend (Python — `apps/engine`)

* Use **type hints** throughout.
* Keep responsibilities separated:

  * `pipeline.py` — DeepMine ingestion
  * `rag.py` — retrieval & answer composition
  * `vectorizer.py` — embeddings integration
  * `store_pg.py` — Postgres/pgvector I/O
  * `validators/*` — capsule contract validation/auto‑fix
* Prefer async I/O for DB/network paths.
* Update/add tests in `apps/engine/tests/` when behavior changes. 

### 7.2 Frontend (TypeScript/React — `app/`)

* Use TypeScript everywhere; avoid `any` unless unavoidable.
* Reuse shared components in `components/ui/`; place interface‑specific components in `components/` or `app/components/`.
* Keep API access and state helpers in `lib/*`.
* Update/add tests in `__tests__` (Vitest) for core flows. 

### 7.3 Docs

Update docs whenever you change behavior, env vars, endpoints, or deployment steps:

* `docs/api-reference.md`, `docs/env-reference.md`, `docs/deployment.md`, `docs/user-guide.md`, examples under `docs/examples/`.

Also keep `config/.env.example` in sync with any environment‑variable changes. 

---

## 8) Git & Branching

1. Branch from **`main`**.
2. Use clear names:

   * `feature/<short-name>`
   * `fix/<issue-or-bug>`
   * `docs/<topic>`
   * `refactor/<area>`
3. Prefer **Conventional Commits**, e.g. `feat(engine): add semantic link suggester`.
4. Rebase on `main` before opening/updating your PR to keep history clean. 

---

## 9) Pull Request Checklist

Before opening a PR, please confirm:

* [ ] My branch is up to date with `main` (rebased or merged). 
* [ ] `npm run test:all` passes locally. 
* [ ] DB changes (if any) are captured in a **new** `infra/sql/*` migration and verified locally with `scripts/migrate.*` and `scripts/verify_migrations.*`. 
* [ ] Env changes are reflected in **both** `config/.env.example` and `docs/env-reference.md`. 
* [ ] No secrets or `.env` files are committed.
* [ ] Tests/docs updated where behavior or config changed.
* [ ] I used the repo’s [PR template](.github/pull_request_template.md) and explained what/why/how clearly. 

---

## 10) Reporting Bugs & Requesting Features

Use GitHub Issues and the provided templates:

* Bug reports: `.github/ISSUE_TEMPLATE/bug_report.md`
* Feature requests: `.github/ISSUE_TEMPLATE/feature_request.md`

Include OS, Python/Node/Docker versions, how you started the stack (scripts vs manual), logs (redacted), and minimal repro steps. 

---

## 11) Security & Privacy

* **Never** commit secrets (API keys, tokens, `.env` files).
* Redact sensitive data in logs/screenshots attached to issues/PRs.
* Use demo/synthetic data; avoid real PII (see `examples/demo-dataset/`). 

If you suspect a security issue, don’t post exploit details publicly. Open a short issue indicating a potential security concern and request a private channel for follow‑up.

---

## 12) Maintaining This File (CONTRIBUTING.md)

If you change how contributors should run tests, migrations, or dev scripts—or you adjust required tools/versions—**update this file** to match, and keep it in sync with the root README and docs. Treat this as the single source of truth for the contribution process.

Thank you for helping build **N1Hub.com**!

````

---

### How to publish this file

From a local clone:

```bash
# from repo root
git checkout -b docs/update-contributing
printf "%s" "<PASTE THE MARKDOWN ABOVE>" > CONTRIBUTING.md
git add CONTRIBUTING.md
git commit -m "docs(contributing): up-to-date contributor guide (dev, tests, migrations, CI)"
git push -u origin docs/update-contributing
# open a PR to main
````

This guide harmonizes the current README quickstart, the existing contributing draft, and the repository tree snapshot so the commands and paths reflect the actual project state today.
