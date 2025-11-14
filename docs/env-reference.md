# N1Hub v0.1 Environment Variables Reference

Полная справка по environment variables для N1Hub v0.1 deployment.

---

## Содержание

1. [Обзор](#обзор)
2. [Глобальная таблица переменных](#глобальная-таблица-переменных)
3. [Environment Matrices](#environment-matrices)
4. [Validation](#validation)
5. [Backend Production Environment](#backend-production-environment)
6. [Frontend Production Environment](#frontend-production-environment)

---

## Обзор

N1Hub v0.1 использует environment variables для конфигурации backend (engine) и frontend (interface). Переменные загружаются из:

- **Backend**: `config/.env` (local) или environment variables на Railway/Render
- **Frontend**: Vercel environment variables (Project Settings → Environment Variables)

**Источники env vars в коде:**
- `apps/engine/app/config.py` – Backend settings класс
- `vercel.json` – Frontend env references
- `scripts/validate_env.py` – Validation script

**Naming convention:**
- `N1HUB_*` – Backend-specific (engine)
- `NEXT_PUBLIC_*` – Frontend-specific, доступны client-side
- `ENGINE_BASE_URL` – Server-side frontend variable

---

## Глобальная таблица переменных

| Переменная | Используется в | Описание | Обязательна | Scope |
|------------|----------------|----------|-------------|-------|
| `STORE_BACKEND` | `apps/engine/app/main.py` | Тип хранилища: `postgres` или `memory` | Yes (backend) | engine |
| `N1HUB_POSTGRES_DSN` | `apps/engine/app/config.py`, `apps/engine/app/store_pg.py` | PostgreSQL connection string | Yes (backend) | engine |
| `N1HUB_REDIS_URL` | `apps/engine/app/middleware.py`, `apps/engine/app/main.py` | Redis connection URL для rate limiting | No | engine |
| `N1HUB_LLM_PROVIDER` | `apps/engine/app/config.py`, `apps/engine/app/rag.py` | LLM провайдер: `anthropic` или `openai` | No | engine |
| `N1HUB_LLM_API_KEY` | `apps/engine/app/config.py`, `apps/engine/app/rag.py` | API ключ для LLM | No | engine |
| `N1HUB_LLM_MODEL` | `apps/engine/app/config.py`, `apps/engine/app/rag.py` | Название модели LLM | No | engine |
| `N1HUB_PUBLIC_SCORE_THRESHOLD` | `apps/engine/app/config.py`, `apps/engine/app/rag.py` | Score threshold для public scope queries | No | engine |
| `N1HUB_RETENTION_DAYS` | `apps/engine/app/config.py`, `apps/engine/app/retention.py` | Срок хранения artifacts (дни) | No | engine |
| `N1HUB_RATE_LIMIT_UPLOAD` | `apps/engine/app/config.py`, `apps/engine/app/middleware.py` | Rate limit для upload (req/min) | No | engine |
| `N1HUB_RATE_LIMIT_CHAT` | `apps/engine/app/config.py`, `apps/engine/app/middleware.py` | Rate limit для chat (req/min) | No | engine |
| `N1HUB_RATE_LIMIT_PUBLIC` | `apps/engine/app/config.py`, `apps/engine/app/middleware.py` | Rate limit для public queries (req/min) | No | engine |
| `N1HUB_MAX_CONCURRENT_JOBS` | `apps/engine/app/config.py`, `apps/engine/app/main.py` | Макс. одновременных jobs на пользователя | No | engine |
| `N1HUB_MAX_PAYLOAD_MB` | `apps/engine/app/config.py`, `apps/engine/app/main.py` | Макс. размер payload (MB) | No | engine |
| `N1HUB_RAG_CHUNK_SIZE` | `apps/engine/app/config.py` | Chunk size для RAG retrieval | No | engine |
| `N1HUB_RAG_CHUNK_STRIDE` | `apps/engine/app/config.py` | Chunk stride для RAG retrieval | No | engine |
| `N1HUB_RAG_RETRIEVER_TOP_K` | `apps/engine/app/config.py` | Top K chunks для retrieval | No | engine |
| `NEXT_PUBLIC_API_URL` | `lib/api.ts`, `vercel.json` | Backend API base URL | Yes (frontend) | app |
| `NEXT_PUBLIC_SSE_URL` | `lib/api.ts`, `vercel.json` | SSE events URL (обычно = API_URL) | No | app |
| `ENGINE_BASE_URL` | `app/api/**`, `vercel.json` | Backend URL для server-side routes | No | app |

---

## Environment Matrices

### Matrix 1: Deployment Environments

| Переменная | LOCAL_DEV | BACKEND_PROD | FRONTEND_PROD |
|------------|-----------|--------------|---------------|
| `STORE_BACKEND` | `postgres` | `postgres` | N/A |
| `N1HUB_POSTGRES_DSN` | `postgresql://postgres:postgres@localhost:5432/n1hub` | `postgresql://user:pass@host.railway.app:5432/railway` | N/A |
| `N1HUB_REDIS_URL` | `redis://localhost:6379/0` | `redis://default:pass@containers-us-west-123.railway.app:6379` | N/A |
| `N1HUB_LLM_PROVIDER` | `anthropic` | `anthropic` | N/A |
| `N1HUB_LLM_API_KEY` | `sk-ant-api03-...` (local test) | `sk-ant-api03-...` (prod) | N/A |
| `N1HUB_LLM_MODEL` | `claude-3-haiku-20240307` | `claude-3-haiku-20240307` | N/A |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | N/A | `https://api.n1hub.com` |
| `NEXT_PUBLIC_SSE_URL` | `http://127.0.0.1:8000` | N/A | `https://api.n1hub.com` |
| `ENGINE_BASE_URL` | N/A (not used locally) | N/A | `https://api.n1hub.com` |

**Примечания:**
- LOCAL_DEV: Используем Docker Compose для Postgres + Redis
- BACKEND_PROD: Railway/Render предоставляют connection strings автоматически
- FRONTEND_PROD: Vercel environment variables (Project Settings)

### Matrix 2: Optional Features

| Переменная | Default Value | Production Recommendation | Описание |
|------------|---------------|---------------------------|----------|
| `N1HUB_PUBLIC_SCORE_THRESHOLD` | `0.62` | `0.62` | Порог для public scope (higher = more selective) |
| `N1HUB_RETENTION_DAYS` | `7` | `7` или `30` | Срок хранения artifacts (7 дней достаточно) |
| `N1HUB_RATE_LIMIT_UPLOAD` | `60` | `60` | Upload limit (req/min per user) |
| `N1HUB_RATE_LIMIT_CHAT` | `60` | `60` | Chat limit (req/min per user) |
| `N1HUB_RATE_LIMIT_PUBLIC` | `120` | `120` | Public scope global limit (req/min) |
| `N1HUB_MAX_CONCURRENT_JOBS` | `10` | `10` | Макс. одновременных jobs на пользователя |
| `N1HUB_MAX_PAYLOAD_MB` | `20` | `20` | Макс. размер payload (MB) |
| `N1HUB_RAG_CHUNK_SIZE` | `800` | `800` | Chunk size (characters) |
| `N1HUB_RAG_CHUNK_STRIDE` | `200` | `200` | Chunk stride/overlap (characters) |
| `N1HUB_RAG_RETRIEVER_TOP_K` | `6` | `6` | Top K chunks для initial retrieval |

**Рекомендации по настройке:**
- **Rate limits**: Увеличьте для высоконагруженных сред
- **Retention**: 7 дней для privacy-first, 30 дней для debugging
- **RAG parameters**: Defaults оптимизированы, изменяйте только при A/B тестировании

---

## Validation

Используйте `scripts/validate_env.py` для проверки переменных окружения.

### Проверка backend

\`\`\`bash
# Local development
python scripts/validate_env.py --target backend

# Production (с .env file)
python scripts/validate_env.py --target backend --env-file .env.production
\`\`\`

**Ожидаемый вывод:**

\`\`\`
==============================================================
Backend Environment Variables
==============================================================
✓ N1HUB_POSTGRES_DSN: postgresql://postgres:...
⚠ N1HUB_REDIS_URL: NOT SET (optional)
  Note: Rate limiting will fall back to in-memory store
⚠ N1HUB_LLM_API_KEY: NOT SET (optional)
  Note: LLM features will be disabled without this

==============================================================
Validation Summary
==============================================================
✓ No errors found

⚠ Warnings: 2
  - Optional: N1HUB_REDIS_URL - Redis connection URL (optional, falls back to in-memory)
  - Optional: N1HUB_LLM_API_KEY - LLM API key (required if using LLM features)

==============================================================
Validation PASSED
==============================================================

Note: Some optional variables are not set. This is OK for basic functionality.
\`\`\`

### Проверка frontend

\`\`\`bash
# Local development
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 python scripts/validate_env.py --target frontend

# Production
python scripts/validate_env.py --target frontend --env-file .env.vercel
\`\`\`

### Проверка всех переменных

\`\`\`bash
python scripts/validate_env.py --target all --env-file .env.production
\`\`\`

### Типичные ошибки валидации

#### Ошибка: Missing required variable

\`\`\`
✗ N1HUB_POSTGRES_DSN: MISSING (required)
  Example: postgresql://user:pass@host:5432/dbname
\`\`\`

**Решение:**
\`\`\`bash
export N1HUB_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/n1hub
\`\`\`

#### Ошибка: Invalid DATABASE_URL format

\`\`\`
✗ N1HUB_POSTGRES_DSN: INVALID FORMAT
  Current: postgres://wrong-format
  Expected: postgresql://user:pass@host:5432/dbname
\`\`\`

**Решение:** Используйте правильный формат `postgresql://` (не `postgres://`)

#### Предупреждение: LLM features disabled

\`\`\`
⚠ N1HUB_LLM_API_KEY: NOT SET (optional)
  Note: LLM features will be disabled without this
\`\`\`

**Решение (если нужны LLM features):**
\`\`\`bash
export N1HUB_LLM_PROVIDER=anthropic
export N1HUB_LLM_API_KEY=sk-ant-api03-...
export N1HUB_LLM_MODEL=claude-3-haiku-20240307
\`\`\`

---

## Backend Production Environment

### Обязательные переменные

\`\`\`env
STORE_BACKEND=postgres
N1HUB_POSTGRES_DSN=postgresql://user:password@host:5432/dbname
\`\`\`

**Где взять `N1HUB_POSTGRES_DSN`:**
- **Railway**: Dashboard → PostgreSQL service → Variables → `DATABASE_URL`
- **Render**: Dashboard → PostgreSQL → Connection Info → `Internal Database URL`

### Опциональные но рекомендуемые

\`\`\`env
# Redis для rate limiting
N1HUB_REDIS_URL=redis://default:password@host:6379

# LLM features (Anthropic)
N1HUB_LLM_PROVIDER=anthropic
N1HUB_LLM_API_KEY=sk-ant-api03-...
N1HUB_LLM_MODEL=claude-3-haiku-20240307

# Или OpenAI
N1HUB_LLM_PROVIDER=openai
N1HUB_LLM_API_KEY=sk-proj-...
N1HUB_LLM_MODEL=gpt-4o-mini
\`\`\`

### Опциональные production tuning

\`\`\`env
# Rate limiting
N1HUB_RATE_LIMIT_UPLOAD=60
N1HUB_RATE_LIMIT_CHAT=60
N1HUB_RATE_LIMIT_PUBLIC=120

# Job management
N1HUB_MAX_CONCURRENT_JOBS=10
N1HUB_MAX_PAYLOAD_MB=20

# Retention policy
N1HUB_RETENTION_DAYS=7
\`\`\`

---

## Frontend Production Environment

### Обязательные переменные (Vercel)

\`\`\`env
NEXT_PUBLIC_API_URL=https://api.n1hub.com
\`\`\`

**Где установить:** Vercel Dashboard → Project Settings → Environment Variables

### Опциональные переменные

\`\`\`env
# SSE events URL (обычно = API_URL)
NEXT_PUBLIC_SSE_URL=https://api.n1hub.com

# Server-side API URL (для Next.js API routes)
ENGINE_BASE_URL=https://api.n1hub.com
\`\`\`

**Примечание:**
- `NEXT_PUBLIC_*` переменные доступны client-side (browser)
- `ENGINE_BASE_URL` доступна только server-side (Next.js API routes)

---

## Troubleshooting Environment Variables

### Проблема: Backend не подключается к базе данных

**Симптомы:**
- `/healthz` возвращает `"status": "degraded"`
- Ошибка: `"database": {"status": "unhealthy"}`

**Диагностика:**
\`\`\`bash
# Проверяем переменную
echo $N1HUB_POSTGRES_DSN

# Тестируем подключение
psql $N1HUB_POSTGRES_DSN -c "SELECT 1;"

# Проверяем валидацию
python scripts/validate_env.py --target backend
\`\`\`

**Решение:**
1. Проверьте правильность connection string
2. Убедитесь, что база данных доступна из deployment platform
3. Проверьте firewall rules (Railway/Render обычно открыты)

### Проблема: Frontend не может подключиться к backend

**Симптомы:**
- CORS errors в browser console
- Ошибка: `Failed to fetch`

**Диагностика:**
\`\`\`bash
# Проверяем переменную в Vercel
vercel env ls

# Тестируем backend напрямую
curl https://api.n1hub.com/healthz
\`\`\`

**Решение:**
1. Убедитесь, что `NEXT_PUBLIC_API_URL` точно соответствует backend URL (с `https://`, без trailing slash)
2. Проверьте, что backend доступен по этому URL
3. Проверьте CORS настройки backend (должен разрешать frontend domain)

### Проблема: LLM features не работают

**Симптомы:**
- Chat возвращает `"answer": "idk+dig_deep"` вместо полноценного ответа
- В логах: `LLM API key not configured`

**Диагностика:**
\`\`\`bash
# Проверяем переменные
echo $N1HUB_LLM_PROVIDER
echo $N1HUB_LLM_API_KEY | cut -c1-15

# Проверяем валидацию
python scripts/validate_env.py --target backend
\`\`\`

**Решение:**
1. Установите `N1HUB_LLM_API_KEY` в backend environment
2. Проверьте, что ключ валидный:
   - Anthropic: https://console.anthropic.com/
   - OpenAI: https://platform.openai.com/account/api-keys
3. Убедитесь, что `N1HUB_LLM_PROVIDER` соответствует ключу (`anthropic` или `openai`)

---

## Best Practices

1. **Never commit secrets to Git**: Используйте `.env` файлы локально, но добавьте их в `.gitignore`
2. **Use .env.example templates**: Commit example files без реальных secrets
3. **Rotate credentials regularly**: Обновляйте API ключи каждые 3-6 месяцев
4. **Use different keys per environment**: Не используйте production keys в development
5. **Validate before deployment**: Всегда запускайте `validate_env.py` перед deploy
6. **Document custom variables**: Если добавляете новые переменные, обновите этот документ

---

## Поддержка

При возникновении проблем с environment variables:
- Проверьте [Deployment Guide](deployment.md#environment-variables-reference)
- Запустите `scripts/validate_env.py --target all`
- Откройте [GitHub Issue](https://github.com/num1hub/n1hub.com/issues) с описанием проблемы

---

**Последнее обновление:** v0.1.0 (на основе реальных файлов `apps/engine/app/config.py`, `vercel.json`, `scripts/validate_env.py`)
\`\`\`

Из-за лимита размера ответа, продолжу создание оставшихся deliverables в следующем сообщении. Уже создано:

1. **README.md** – Полный production-ready root README
2. **docs/env-reference.md** – Comprehensive environment variables reference

Осталось создать еще 6 deliverables + integration checklist.
