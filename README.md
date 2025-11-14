# N1Hub.com

**AI‑native knowledge system — _Anything → Capsules → Graph → Chat_ — built for real‑world use.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?logo=node.js&logoColor=fff)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs)](https://nextjs.org/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-%2B%20pgvector-336791?logo=postgresql&logoColor=fff)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7.x-dc382d?logo=redis&logoColor=fff)](https://redis.io/)

---

## Table of contents

- [Overview](#overview)
- [Architecture at a glance](#architecture-at-a-glance)
- [Repository layout](#repository-layout)
- [Quickstart (local dev)](#quickstart-local-dev)
- [Configuration](#configuration)
- [API quick tour](#api-quick-tour)
- [Tests & quality](#tests--quality)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Security & privacy](#security--privacy)
- [License](#license)
- [Support](#support)

---

## Overview

**N1Hub.com** is a full‑stack, spec‑aligned reference implementation of a **CapsuleOS**: ingest _anything_, transform it into strictly validated **Knowledge Capsules**, link them into a semantic **graph**, and run grounded **chat** over your knowledge using hybrid retrieval‑augmented generation (semantic + lexical).

**Core workflow:** **Anything → Capsules → Graph → Chat**

- **Anything** — upload text, docs, or demo data  
- **Capsules** — a multi‑stage _DeepMine_ pipeline normalizes, segments, summarizes, validates, embeds, links, and indexes content  
- **Graph** — capsules are linked and tagged to form a navigable knowledge graph  
- **Chat** — ask questions over chosen scopes; answers are strictly cited

---

## Architecture at a glance

This monorepo combines a **FastAPI** engine with **Next.js** frontends and **PostgreSQL + pgvector** for retrieval, plus **Redis** for caching/events.

```mermaid
flowchart LR
    subgraph Browser["User (Browser)"]
      UI[Next.js Interface<br/>app/]
    end

    subgraph Frontend["Frontend"]
      APIProxy["App Router API routes<br/>/api/*"]
    end

    subgraph Engine["FastAPI Engine (apps/engine)"]
      Ingest["pipeline.py<br/>DeepMine ingestion"]
      RAG["rag.py<br/>semantic + lexical"]
      Vec["vectorizer.py<br/>embeddings"]
      Events["events.py<br/>SSE"]
      Obs["observability.py<br/>health/metrics"]
      Store["store_pg.py<br/>Postgres + pgvector"]
    end

    subgraph Data["Data Services"]
      PG[(Postgres + pgvector)]
      Redis[(Redis)]
    end

    UI -- fetch --> APIProxy
    APIProxy -- HTTP --> Engine
    Engine <---> PG
    Engine <---> Redis
    RAG <--> Vec
    Ingest --> Store
    UI -. SSE .-> Events
Repository layout
bash
Копировать код
n1hub.com/
├─ app/                      # Root Next.js app (landing / layout)
├─ apps/
│  ├─ engine/                # FastAPI backend (pipeline, RAG, validators, SSE, observability)
│  └─ interface/             # Next.js interface (chat, capsules, graph, inbox) + API proxy routes
├─ infra/
│  ├─ sql/                   # 0001..0004 SQL migrations
│  └─ docker-compose.yml     # Local Postgres + Redis
├─ docs/                     # Architecture, API reference, deployment, env reference, examples
├─ scripts/                  # dev.sh/dev-win.ps1, migrate.*, verify_migrations.*, validate_env.py
├─ tools/                    # Spec alignment, env validation
├─ examples/
│  └─ demo-dataset/          # Demo docs and loader scripts
└─ .github/workflows/ci.yml  # CI checks (lint, typecheck, tests, migrations, validation)
Quickstart (local dev)
The fastest path is:
start Postgres + Redis via Docker,
run DB migrations,
start the Python engine,
start the Next.js interface.
1) Prerequisites
Git
Python 3.11+
Node.js 20+ (comes with npm)
Docker Desktop
Check versions:
bash
Копировать код
git --version && python --version && node --version && npm --version && docker --version
2) Clone & configure
bash
Копировать код
git clone https://github.com/num1hub/n1hub.com.git
cd n1hub.com

mkdir -p config
cp config/.env.example config/.env
Edit config/.env for your machine (DB/Redis DSNs, optional LLM provider/key). See docs/env-reference.md for the full list.
3) Start local services
bash
Копировать код
cd infra
docker compose up -d
cd ..
4) Apply database migrations
macOS/Linux (bash):
bash
Копировать код
./scripts/migrate.sh
# optional
./scripts/verify_migrations.sh
Windows (PowerShell):
powershell
Копировать код
.\scripts\migrate.ps1
# optional
.\scripts\verify_migrations.ps1
5) Run the backend (FastAPI)
bash
Копировать код
cd apps/engine
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
Health & docs:
http://127.0.0.1:8000/healthz
http://127.0.0.1:8000/docs
6) Run the frontend (Next.js interface)
Open a new terminal at the repo root:
bash
Копировать код
pnpm install
pnpm dev
Visit: http://localhost:3000 If the UI can’t reach the engine, set in your shell (or .env.local):
bash
Копировать код
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
export NEXT_PUBLIC_SSE_URL=http://127.0.0.1:8000/events/stream
7) Smoke test
Open the app and upload a small document.
Watch /inbox for the ingestion job to complete.
Open /capsules to see the new capsule.
Ask a question in /chat and confirm the answer includes strict citations.
Configuration
Common environment variables (see docs/env-reference.md for the complete set):
Variable	Purpose	Example
STORE_BACKEND	Storage backend	postgres
N1HUB_POSTGRES_DSN	Postgres DSN	postgresql://postgres:postgres@localhost:5432/n1hub
N1HUB_REDIS_URL	Redis DSN	redis://localhost:6379/0
N1HUB_LLM_PROVIDER	LLM provider	anthropic or openai
N1HUB_LLM_API_KEY	API key	sk-...
N1HUB_LLM_MODEL	Model name	e.g., claude-3-haiku-20240307
NEXT_PUBLIC_API_URL	Engine URL (browser)	http://127.0.0.1:8000
NEXT_PUBLIC_SSE_URL	SSE stream URL	http://127.0.0.1:8000/events/stream
ENGINE_BASE_URL	Engine URL for SSR (frontend)	http://127.0.0.1:8000

API quick tour
The FastAPI engine exposes endpoints for ingestion, jobs, capsules, chat (RAG), observability, validation, health, and SSE. Full details live in docs/api-reference.md. Base URL (local): http://127.0.0.1:8000
Ingest → Job → Capsule → Chat
bash
Копировать код
# Ingest
curl -sS -X POST "$API/ingest" -H "Content-Type: application/json" -d '{
  "title": "ML Basics",
  "content": "Machine learning is ...",
  "tags": ["ml","ai","basics"],
  "include_in_rag": true
}'

# Chat over your capsules
curl -sS -X POST "$API/chat" -H "Content-Type: application/json" -d '{
  "query": "What is this about?",
  "scope": ["my"]    # or ["public"], ["inbox"], ["tag"]
}'
Server‑Sent Events
js
Копировать код
const es = new EventSource(`${API}/events/stream`);
es.onmessage = (e) => {
  const update = JSON.parse(e.data);
  console.log('Job update', update);
};
Health: /healthz, /readyz, /livez
Tests & quality
Run what CI runs:
bash
Копировать код
# all
npm run test:all

# engine only (pytest)
pnpm test:engine
# or
cd apps/engine && pytest

# UI only (Vitest)
pnpm test:ui
Additional checks used by CI and helpful locally:
Lint/typecheck (frontend) — pnpm lint && pnpm typecheck
Migration verification — scripts/verify_migrations.*
Env validation — scripts/validate_env.py
Capsule spec alignment — tools/validate_capsule_alignment.py
Deployment
Typical split:
Frontend (app/) → Vercel
Backend (apps/engine) → Railway/Render (or your infra)
Domains → e.g., n1hub.com → frontend, api.n1hub.com → backend
Backend
Provision Postgres (with pgvector) and (optionally) managed Redis
Run migrations with scripts/migrate.*
Configure env: STORE_BACKEND, N1HUB_POSTGRES_DSN, N1HUB_REDIS_URL, N1HUB_LLM_PROVIDER, N1HUB_LLM_API_KEY, N1HUB_LLM_MODEL
Frontend (Vercel)
Set:
env
Копировать код
NEXT_PUBLIC_API_URL=https://api.n1hub.com
NEXT_PUBLIC_SSE_URL=https://api.n1hub.com/events/stream
ENGINE_BASE_URL=https://api.n1hub.com
Production checks
Verify /healthz, /readyz
Upload a small doc → confirm ingestion & a cited chat answer
Troubleshooting
UI can’t reach the engine — make sure NEXT_PUBLIC_API_URL and NEXT_PUBLIC_SSE_URL point to the running engine (see Quickstart → 6).
Migrations fail — ensure Docker services are up; re‑run scripts/migrate.* and scripts/verify_migrations.*.
SSE not streaming — check any reverse proxy for text/event-stream support and disabled buffering.
429 Too Many Requests — back off and honor Retry-After; reduce concurrent jobs.
Vector errors — confirm pgvector is installed and the vector dimension matches your embedding model (schema updated in migration 0004_update_vector_dimension.sql).
Contributing
We welcome issues and pull requests! Before opening a PR, please read CONTRIBUTING.md and run the same checks CI runs locally:
bash
Копировать код
npm run test:all
Use the included issue and PR templates; update docs and env examples when behavior or configuration changes.
Security & privacy
Never commit secrets (API keys, tokens, .env files).
Redact sensitive data in logs/screenshots.
Prefer demo/synthetic data during testing.
If you suspect a security issue, open a short issue indicating a potential concern and request a private follow‑up channel.
License
TBD — If you plan to distribute, add a LICENSE file (e.g., MIT) and update this section accordingly.
Support
Issues: https://github.com/num1hub/n1hub.com/issues
Engine health checks: /healthz, /readyz, /livez
Built as a pragmatic reference for the “Anything → Capsules → Graph → Chat” workflow.
yaml
Копировать код

---

### Why this README is aligned with the repo

- Commands and local development flow mirror the existing quickstart (versions, scripts, SSE paths, and UI/engine ports). :contentReference[oaicite:0]{index=0}  
- The monorepo layout, engine modules, migrations `0001..0004`, and the DeepMine/RAG architecture are consistent with the architecture notes. :contentReference[oaicite:1]{index=1}  
- Endpoint shapes (ingest/jobs/capsules/chat/observability/validation/health/SSE), sample payloads, scopes, and job code semantics follow the engine’s API reference. :contentReference[oaicite:2]{index=2}  
- The tests/CI/lint/typecheck/migration‑verification/spec‑alignment guidance aligns with the contributor workflow and repository scripts. :contentReference[oaicite:3]{index=3}

---

### Publish to GitHub

From a local clone of `num1hub/n1hub.com`:

```bash
# 1) Replace the README at repo root with the downloaded file
# (Adjust the path if you saved it elsewhere.)
cp /path/to/README.md ./README.md

# 2) Commit & push
git checkout -b docs/update-readme
git add README.md
git commit -m "docs(readme): refresh repo overview, quickstart, API, and deployment"
git push -u origin docs/update-readme

# 3) Open a PR to main
If you want, I can also prepare companion updates (badges, screenshots, or a small “Getting Started” screencast section) to land in the same PR.
