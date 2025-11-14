# N1Hub v0.1 Production Deployment Guide

This guide provides step-by-step instructions for deploying N1Hub v0.1 to production using Vercel (frontend) and Railway/Render (backend).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- A GitHub account and repository access
- Vercel account (free tier is sufficient)
- Railway or Render account (free tier available)
- PostgreSQL database with pgvector extension (provided by Railway/Render)
- Redis instance (optional, but recommended)
- LLM API keys (optional - Anthropic or OpenAI)

## Database Setup

### Step 1: Create Database

**Railway:**
1. Create a new project in Railway
2. Add a PostgreSQL service (Railway automatically includes pgvector)
3. Note the `DATABASE_URL` connection string

**Render:**
1. Create a new PostgreSQL database
2. Select PostgreSQL 16 with pgvector extension
3. Note the `Internal Database URL` connection string

### Step 2: Run Migrations

Before deploying the backend, run database migrations:

\`\`\`bash
# Using the migration script
./scripts/migrate.sh --database-url "postgresql://user:pass@host:5432/dbname"

# Or on Windows
.\scripts\migrate.ps1 -DatabaseUrl "postgresql://user:pass@host:5432/dbname"
\`\`\`

**Verify migrations:**
\`\`\`bash
./scripts/verify_migrations.sh --database-url "postgresql://user:pass@host:5432/dbname"
\`\`\`

Expected output:
\`\`\`
✓ Extension installed: uuid-ossp
✓ Extension installed: vector
✓ Table exists: capsules (rows: 0)
✓ Table exists: capsule_vectors (rows: 0)
✓ Table exists: links (rows: 0)
✓ Table exists: jobs (rows: 0)
✓ Table exists: artifacts (rows: 0)
✓ Table exists: query_logs (rows: 0)
✓ Table exists: validation_runs (rows: 0)
✓ Table exists: link_suggestions (rows: 0)
✓ Table exists: audit_logs (rows: 0)
✓ All migrations verified successfully
\`\`\`

## Backend Deployment

### Option A: Railway

1. **Connect Repository:**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your N1Hub repository

2. **Configure Service:**
   - Railway will detect `railway.toml` automatically
   - Add PostgreSQL service (if not already added)
   - Add Redis service (optional)

3. **Set Environment Variables:**
   Go to your service → Variables tab and add:
   \`\`\`
   STORE_BACKEND=postgres
   N1HUB_POSTGRES_DSN=${{Postgres.DATABASE_URL}}
   N1HUB_REDIS_URL=${{Redis.REDIS_URL}}  # Optional
   N1HUB_LLM_PROVIDER=anthropic  # Optional
   N1HUB_LLM_API_KEY=sk-...  # Optional
   N1HUB_LLM_MODEL=claude-3-haiku-20240307  # Optional
   \`\`\`

4. **Deploy:**
   - Railway will automatically deploy on push to main branch
   - Or click "Deploy" manually

5. **Get Backend URL:**
   - Railway provides a public URL (e.g., `https://n1hub-engine.up.railway.app`)
   - Note this URL for frontend configuration

### Option B: Render

1. **Create Web Service:**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically

2. **Configure Service:**
   - Render will create PostgreSQL and Redis services from `render.yaml`
   - Environment variables are set automatically from service references

3. **Manual Environment Variables (if needed):**
   \`\`\`
   STORE_BACKEND=postgres
   N1HUB_LLM_PROVIDER=anthropic  # Optional
   N1HUB_LLM_API_KEY=sk-...  # Optional
   N1HUB_LLM_MODEL=claude-3-haiku-20240307  # Optional
   \`\`\`

4. **Deploy:**
   - Render will deploy automatically
   - Get the public URL (e.g., `https://n1hub-engine.onrender.com`)

### Verify Backend Deployment

1. **Health Check:**
   \`\`\`bash
   curl https://your-backend-url.com/healthz
   \`\`\`
   Expected response:
   \`\`\`json
   {
     "status": "ok",
     "timestamp": "2024-01-01T00:00:00Z",
     "components": {
       "database": {"status": "healthy"},
       "redis": {"status": "healthy"},
       "pgvector": {"status": "healthy"}
     }
   }
   \`\`\`

2. **Readiness Check:**
   \`\`\`bash
   curl https://your-backend-url.com/readyz
   \`\`\`
   Should return `200 OK` with `"status": "ready"`

## Frontend Deployment

### Vercel Deployment

1. **Connect Repository:**
   - Go to Vercel dashboard
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will detect Next.js automatically

2. **Configure Build Settings:**
   - Framework Preset: Next.js
   - Root Directory: `.` (root App Router)
   - Build Command: `pnpm run build`
   - Output Directory: `.next`

3. **Set Environment Variables:**
   Go to Project Settings → Environment Variables:
   \`\`\`
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   NEXT_PUBLIC_SSE_URL=https://your-backend-url.com
   ENGINE_BASE_URL=https://your-backend-url.com
   \`\`\`

4. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Get the public URL (e.g., `https://n1hub.vercel.app`)

### Verify Frontend Deployment

1. Visit your Vercel URL
2. Check browser console for errors
3. Test the upload flow
4. Test the chat functionality

## Post-Deployment Verification

### 1. Environment Validation

Validate environment variables:

\`\`\`bash
# Backend
python scripts/validate_env.py --target backend --env-file .env.production

# Frontend
python scripts/validate_env.py --target frontend --env-file .env.production
\`\`\`

### 2. End-to-End Testing

1. **Upload Test:**
   - Go to frontend `/inbox`
   - Upload a test document
   - Verify job completes successfully

2. **Capsule View:**
   - Go to `/capsules`
   - Verify capsules are displayed
   - Check capsule details

3. **Chat Test:**
   - Go to `/chat`
   - Ask a question about your capsules
   - Verify answer with citations

4. **Graph View:**
   - Go to `/graph`
   - Verify capsule graph is displayed

### 3. Observability Checks

\`\`\`bash
# Retrieval metrics
curl https://your-backend-url.com/observability/retrieval

# Router diagnostics
curl https://your-backend-url.com/observability/router

# Semantic hash integrity
curl https://your-backend-url.com/observability/semantic-hash

# PII scan
curl https://your-backend-url.com/observability/pii
\`\`\`

## Troubleshooting

### Database Connection Issues

**Problem:** Backend can't connect to database

**Solutions:**
1. Verify `N1HUB_POSTGRES_DSN` is set correctly
2. Check database is accessible from deployment platform
3. Verify migrations have run: `./scripts/verify_migrations.sh`
4. Check database logs for connection errors

### Migration Failures

**Problem:** Migrations fail with "already exists" errors

**Solution:** Migrations are idempotent - this is normal. Check if tables exist:
\`\`\`bash
./scripts/verify_migrations.sh --database-url $DATABASE_URL
\`\`\`

### pgvector Extension Missing

**Problem:** `pgvector extension not installed`

**Solutions:**
1. **Railway:** pgvector is included automatically
2. **Render:** Ensure PostgreSQL 16 with pgvector is selected
3. **Manual:** Run `CREATE EXTENSION IF NOT EXISTS vector;` in database

### Frontend Can't Connect to Backend

**Problem:** CORS errors or connection refused

**Solutions:**
1. Verify `NEXT_PUBLIC_API_URL` matches backend URL exactly
2. Check backend CORS settings (should allow frontend domain)
3. Verify backend is running and accessible
4. Check browser console for specific error messages

### Health Check Failing

**Problem:** `/healthz` returns `degraded` or `unhealthy`

**Solutions:**
1. Check component status in response:
   \`\`\`json
   {
     "components": {
       "database": {"status": "unhealthy", "error": "..."}
     }
   }
   \`\`\`
2. Verify database connection string
3. Check Redis connection (optional, won't fail if not configured)
4. Verify pgvector extension is installed

### LLM Features Not Working

**Problem:** Chat returns fallback message instead of LLM-generated answer

**Solutions:**
1. Verify `N1HUB_LLM_API_KEY` is set
2. Check API key is valid and has credits
3. Verify `N1HUB_LLM_PROVIDER` matches API key provider
4. Check backend logs for LLM errors
5. Note: LLM features are optional - system works without them

### Rate Limiting Issues

**Problem:** Too many requests errors

**Solutions:**
1. Check rate limit settings in environment variables
2. Verify Redis is configured (rate limiting uses Redis)
3. Adjust limits if needed:
   \`\`\`
   N1HUB_RATE_LIMIT_UPLOAD=60
   N1HUB_RATE_LIMIT_CHAT=60
   N1HUB_RATE_LIMIT_PUBLIC=120
   \`\`\`

## Environment Variables Reference

### Backend (Required)
- `N1HUB_POSTGRES_DSN` - PostgreSQL connection string
- `STORE_BACKEND=postgres` - Use Postgres store

### Backend (Optional)
- `N1HUB_REDIS_URL` - Redis connection URL
- `N1HUB_LLM_PROVIDER` - "anthropic" or "openai"
- `N1HUB_LLM_API_KEY` - LLM API key
- `N1HUB_LLM_MODEL` - Model name
- `N1HUB_PUBLIC_SCORE_THRESHOLD` - Public scope threshold (default: 0.62)
- `N1HUB_RETENTION_DAYS` - Artifact retention (default: 7)

### Frontend (Required)
- `NEXT_PUBLIC_API_URL` - Backend API URL

### Frontend (Optional)
- `NEXT_PUBLIC_SSE_URL` - SSE events URL (defaults to /api/events)
- `ENGINE_BASE_URL` - Backend URL for server-side API routes

## Next Steps

After successful deployment:

1. **Monitor Health:**
   - Set up monitoring for `/healthz` endpoint
   - Configure alerts for degraded status

2. **Backup Database:**
   - Configure automated backups
   - Test restore procedures

3. **Scale Resources:**
   - Monitor resource usage
   - Scale database/Redis as needed

4. **Update Documentation:**
   - Document your specific deployment URLs
   - Update team on access credentials

## Support

For issues or questions:
- Check [README.md](../README.md) for general information
- Review [Architecture Documentation](./N1Hub-v0.1-architecture.md)
- Check GitHub Issues for known problems
