from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Header, Query, Request, status
from fastapi.responses import StreamingResponse

from .config import settings
from .events import event_publisher
from .feature_flags import feature_flags
from .middleware import RateLimitMiddleware, create_redis_client
from .models import (
    CapsuleModel,
    CapsulePatch,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    JobModel,
    ObservabilityReport,
)
from .observability import (
    pii_report,
    retrieval_metrics,
    router_diagnostics,
    semantic_hash_report,
    standard_reports,
)
from .pipeline import DeepMinePipeline
from .rag import answer_chat
from .retention import retention_cleanup_task
from .routes.validation import validation_router
from .store import BaseCapsuleStore, MemoryCapsuleStore
from .store_pg import PostgresCapsuleStore


def create_store() -> BaseCapsuleStore:
    """Factory function to create the appropriate store backend."""
    if settings.store_backend == "postgres" and settings.postgres_dsn:
        try:
            return PostgresCapsuleStore(settings.postgres_dsn)
        except Exception:
            # Fallback to memory if Postgres connection fails
            return MemoryCapsuleStore()
    return MemoryCapsuleStore()


store = create_store()
redis_client = None

# Initialize rate limiting middleware (must be done before creating app)
async def _init_redis() -> None:
    """Initialize Redis client for rate limiting."""
    global redis_client
    redis_client = await create_redis_client()

# Create app and add middleware
app = FastAPI(title="N1Hub DeepMine Engine", version=settings.engine_version)
pipeline = DeepMinePipeline(store)

# Include validation router
app.include_router(validation_router)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, redis_client=None)  # Will be set on startup


async def _bootstrap_capsules() -> None:
    capsules = await store.list_capsules()
    if capsules:
        return
    # Try to seed from 20-pack if available
    try:
        from .bootstrap import seed_from_pack
        from pathlib import Path
        pack_path = Path("ALL-IN-ONE_CAPSULE_20-pack.json")
        if pack_path.exists():
            await seed_from_pack(store, str(pack_path))
            return
    except Exception:
        pass
    # Fallback to minimal seeds
    seed_materials = [
        {
            "title": "Capsule Schema Contract",
            "content": "The capsule schema contract enforces four sections and mirror hashes. It keeps DeepMine honest and powers retrieval guardrails.",
            "tags": ["schema", "contract", "capsule"],
        },
        {
            "title": "DeepMine Retrieval Defaults",
            "content": "DeepMine uses chunk_size 800, stride 200, retriever top_k 6, mmr 0.3, rerank keep 8, and citations at 0.62 confidence threshold.",
            "tags": ["rag", "defaults", "retrieval"],
        },
    ]
    for material in seed_materials:
        request = IngestRequest(**material, include_in_rag=True)
        job = await store.create_job()
        await pipeline.run(job.id, request)


@app.on_event("startup")
async def on_startup() -> None:
    global redis_client
    redis_client = await create_redis_client()
    await _bootstrap_capsules()
    # Start retention cleanup task
    asyncio.create_task(retention_cleanup_task(store, interval_seconds=3600))


def _get_user_id(request: Request) -> str:
    """Extract user ID from request (IP address for now)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_job_concurrency(user_id: str) -> None:
    """Check if user has exceeded concurrent job limit."""
    jobs = await store.list_jobs()
    # Filter active jobs for this user (simplified: in production, track by user_id)
    active_jobs = [j for j in jobs if j.state in ("processing", "queued")]
    if len(active_jobs) >= settings.max_concurrent_jobs:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {settings.max_concurrent_jobs} concurrent jobs exceeded",
            headers={"Retry-After": "60"},
        )


@app.post("/ingest")
async def ingest(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    request_obj: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """Create ingestion job with idempotency and concurrency checks."""
    # Check payload size (rough estimate)
    payload_size_mb = len(json.dumps(request.model_dump()).encode()) / (1024 * 1024)
    if payload_size_mb > settings.max_payload_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload size {payload_size_mb:.2f}MB exceeds maximum {settings.max_payload_mb}MB",
        )
    
    # Check job concurrency
    user_id = _get_user_id(request_obj)
    await _check_job_concurrency(user_id)
    
    # Check idempotency (if key provided, check for existing job)
    if idempotency_key:
        # In production, store idempotency_key -> job_id mapping in Redis
        # For now, create new job
        pass
    
    # Check feature flag for audio ingest
    if request.source.type == "audio" and not feature_flags.is_enabled("ff.audio.ingest"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audio ingestion is not enabled",
        )
    
    job = await store.create_job()
    await event_publisher.publish_job_update(job)

    async def _runner() -> None:
        try:
            await pipeline.run(job.id, request)
            updated_job = await store.get_job(job.id)
            await event_publisher.publish_job_update(updated_job)
        except Exception as exc:  # pragma: no cover
            await store.update_job(job.id, code=500, stage="failed", state="failed", progress=100, error={"message": str(exc)})
            updated_job = await store.get_job(job.id)
            await event_publisher.publish_job_update(updated_job)

    background_tasks.add_task(_runner)
    return {"job_id": job.id, "state": job.state}


@app.get("/events/stream")
async def events_stream():
    """SSE endpoint for job updates."""
    subscriber_id = str(uuid.uuid4())
    queue = await event_publisher.subscribe(subscriber_id)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            await event_publisher.unsubscribe(subscriber_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/admin/seed/20-pack")
async def seed_20_pack() -> dict:
    """Manually trigger 20-pack seeding."""
    from .bootstrap import seed_from_pack
    from pathlib import Path
    pack_path = Path("ALL-IN-ONE_CAPSULE_20-pack.json")
    if not pack_path.exists():
        raise HTTPException(status_code=404, detail="20-pack file not found")
    await seed_from_pack(store, str(pack_path))
    capsules = await store.list_capsules()
    return {"status": "seeded", "capsule_count": len(capsules)}


@app.get("/jobs", response_model=List[JobModel])
async def list_jobs() -> List[JobModel]:
    return await store.list_jobs()


@app.get("/jobs/{job_id}", response_model=JobModel)
async def get_job(job_id: str) -> JobModel:
    try:
        return await store.get_job(job_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Job not found") from exc


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> dict:
    """Cancel a job if it hasn't reached indexing stage."""
    try:
        job = await store.get_job(job_id)
        # Only allow cancellation if stage < indexing (code < 180)
        if job.code >= 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel job that has reached indexing stage",
            )
        
        # Update job to cancelled state
        await store.update_job(
            job_id,
            code=500,
            stage="cancelled",
            state="cancelled",
            progress=100,
            error={"message": "Job cancelled by user"},
        )
        await event_publisher.publish_job_update(await store.get_job(job_id))
        return {"status": "cancelled", "job_id": job_id}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@app.get("/capsules", response_model=List[CapsuleModel])
async def list_capsules(include_in_rag: Optional[bool] = Query(default=None)) -> List[CapsuleModel]:
    return await store.list_capsules(include_in_rag=include_in_rag)


@app.get("/capsules/{capsule_id}", response_model=CapsuleModel)
async def get_capsule(capsule_id: str) -> CapsuleModel:
    try:
        return await store.get_capsule(capsule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Capsule not found") from exc


@app.patch("/capsules/{capsule_id}", response_model=CapsuleModel)
async def patch_capsule(capsule_id: str, payload: CapsulePatch) -> CapsuleModel:
    """Update capsule with audit logging (Section 4 & 11: API & Security & Privacy Defaults).
    
    Supports updating:
    - include_in_rag: Toggle RAG inclusion
    - tags: Update tags (3-10 items, lowercase, no PII)
    - status: Update status (draft, active, archived)
    """
    try:
        # Get current capsule state for audit logging
        current_capsule = await store.get_capsule(capsule_id)
        old_include_in_rag = current_capsule.include_in_rag
        old_status = current_capsule.metadata.status
        old_tags = current_capsule.metadata.tags.copy()
        
        updated_capsule = current_capsule
        
        # Update include_in_rag if provided
        if payload.include_in_rag is not None:
            updated_capsule = await store.toggle_capsule(capsule_id, payload.include_in_rag)
            # Log RAG toggle change
            if old_include_in_rag != payload.include_in_rag:
                await store.log_audit(
                    capsule_id=capsule_id,
                    action_type="rag_toggle",
                    old_value=str(old_include_in_rag),
                    new_value=str(payload.include_in_rag),
                    actor="system",  # Note: Auth integration pending - will use user context when available
                )
        
        # Update tags if provided
        if payload.tags is not None:
            updated_capsule = await store.update_capsule_tags(capsule_id, payload.tags)
            # Log tag change
            if old_tags != updated_capsule.metadata.tags:
                await store.log_audit(
                    capsule_id=capsule_id,
                    action_type="tags_update",
                    old_value=",".join(old_tags),
                    new_value=",".join(updated_capsule.metadata.tags),
                    actor="system",  # Note: Auth integration pending
                )
        
        # Update status if provided
        if payload.status is not None:
            updated_capsule = await store.update_capsule_status(capsule_id, payload.status)
            # Log status change
            if old_status != payload.status:
                await store.log_audit(
                    capsule_id=capsule_id,
                    action_type="status_change",
                    old_value=old_status,
                    new_value=payload.status,
                    actor="system",  # Note: Auth integration pending
                )
        
        # Ensure we have the latest capsule state
        if payload.include_in_rag is None and payload.tags is None and payload.status is None:
            raise HTTPException(
                status_code=400,
                detail="At least one field (include_in_rag, tags, or status) must be provided"
            )
        
        return await store.get_capsule(capsule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Capsule not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await answer_chat(store, request)


@app.get("/observability/retrieval", response_model=ObservabilityReport)
async def observability_retrieval(window_days: int = Query(default=7, ge=1, le=30)) -> ObservabilityReport:
    """Retrieval metrics with configurable window (7d or 30d)."""
    return await retrieval_metrics(store, window_days=window_days)


@app.get("/observability/router", response_model=ObservabilityReport)
async def observability_router(window_days: int = Query(default=7, ge=1, le=30)) -> ObservabilityReport:
    """Router diagnostics with configurable window (7d or 30d)."""
    return await router_diagnostics(store, window_days=window_days)


@app.get("/observability/semantic-hash", response_model=ObservabilityReport)
async def observability_semantic_hash() -> ObservabilityReport:
    return await semantic_hash_report(store)


@app.get("/observability/pii", response_model=ObservabilityReport)
async def observability_pii() -> ObservabilityReport:
    return await pii_report(store)


@app.get("/observability/standard", response_model=List[ObservabilityReport])
async def observability_standard(window_days: int = Query(default=7, ge=1, le=30)) -> List[ObservabilityReport]:
    """Standard observability reports with configurable window (7d or 30d)."""
    return await standard_reports(store, window_days=window_days)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Enhanced health check with component status (DB, Redis, pgvector)."""
    components = {}
    
    # Check database connectivity
    db_status = "unknown"
    db_error = None
    try:
        await store.list_capsules()
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    components["database"] = {"status": db_status}
    if db_error:
        components["database"]["error"] = db_error
    
    # Check Redis connectivity (optional)
    if redis_client:
        redis_status = "unknown"
        redis_error = None
        try:
            await redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = "unhealthy"
            redis_error = str(e)
        components["redis"] = {"status": redis_status}
        if redis_error:
            components["redis"]["error"] = redis_error
    else:
        components["redis"] = {"status": "not_configured"}
    
    # Check pgvector extension (if Postgres store)
    if isinstance(store, PostgresCapsuleStore):
        vector_status = "unknown"
        vector_error = None
        try:
            # Check if vector extension is available
            test_embedding = [0.0] * settings.embedding_dimension
            # Try to create a test vector (just validation, no actual search)
            import asyncpg
            pool = await store._get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname='vector';")
                if result:
                    vector_status = "healthy"
                else:
                    vector_status = "unhealthy"
                    vector_error = "pgvector extension not installed"
        except Exception as e:
            vector_status = "unhealthy"
            vector_error = str(e)
        components["pgvector"] = {"status": vector_status}
        if vector_error:
            components["pgvector"]["error"] = vector_error
    else:
        components["pgvector"] = {"status": "not_applicable"}
    
    # Overall status: ok if database is healthy (Redis and pgvector are optional)
    overall_status = "ok" if db_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        components=components
    )


@app.get("/livez", response_model=HealthResponse)
async def livez() -> HealthResponse:
    return HealthResponse(status="live", timestamp=datetime.now(timezone.utc))


@app.get("/readyz", response_model=HealthResponse)
async def readyz() -> HealthResponse:
    """Check readiness: DB schema, Redis, and vector index availability.
    
    Returns 200 if ready, 503 if not ready.
    """
    components = {}
    all_ready = True
    
    # Check database connectivity and schema
    db_status = "unknown"
    db_error = None
    schema_ready = False
    try:
        capsules = await store.list_capsules()
        db_status = "healthy"
        # Verify required tables exist (if Postgres)
        if isinstance(store, PostgresCapsuleStore):
            import asyncpg
            pool = await store._get_pool()
            async with pool.acquire() as conn:
                required_tables = ["capsules", "capsule_vectors", "jobs", "query_logs", "audit_logs"]
                existing_tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename=ANY($1::text[]);",
                    required_tables
                )
                existing_table_names = {row["tablename"] for row in existing_tables}
                missing_tables = set(required_tables) - existing_table_names
                if missing_tables:
                    schema_ready = False
                    db_error = f"Missing tables: {', '.join(missing_tables)}"
                else:
                    schema_ready = True
        else:
            schema_ready = True  # Memory store doesn't need schema check
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
        schema_ready = False
    
    components["database"] = {
        "status": db_status,
        "schema_ready": schema_ready
    }
    if db_error:
        components["database"]["error"] = db_error
    
    if not schema_ready:
        all_ready = False
    
    # Check Redis (optional but recommended for production)
    if redis_client:
        redis_status = "unknown"
        redis_error = None
        try:
            await redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = "unhealthy"
            redis_error = str(e)
        components["redis"] = {"status": redis_status}
        if redis_error:
            components["redis"]["error"] = redis_error
        # Redis is optional, so don't fail readiness if it's down
    else:
        components["redis"] = {"status": "not_configured"}
    
    # Check pgvector extension (if Postgres store)
    if isinstance(store, PostgresCapsuleStore):
        vector_status = "unknown"
        vector_error = None
        try:
            import asyncpg
            pool = await store._get_pool()
            async with pool.acquire() as conn:
                # Check if vector extension is installed
                ext_exists = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname='vector';")
                if ext_exists:
                    vector_status = "healthy"
                    # Try a simple vector operation to verify it works (outside transaction)
                    try:
                        test_embedding = [0.0] * settings.embedding_dimension
                        await store.vector_search(test_embedding, top_k=1)
                    except Exception:
                        # Vector search might fail if no capsules, but extension is installed
                        pass
                else:
                    vector_status = "unhealthy"
                    vector_error = "pgvector extension not installed"
        except Exception as e:
            vector_status = "unhealthy"
            vector_error = str(e)
        components["pgvector"] = {"status": vector_status}
        if vector_error:
            components["pgvector"]["error"] = vector_error
        if vector_status != "healthy":
            all_ready = False
    else:
        components["pgvector"] = {"status": "not_applicable"}
    
    # Return readiness status
    if all_ready:
        return HealthResponse(
            status="ready",
            timestamp=datetime.now(timezone.utc),
            components=components
        )
    else:
        # Return 503 status code for not ready
        from fastapi import Response
        return Response(
            content=json.dumps({
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "components": components
            }),
            status_code=503,
            media_type="application/json"
        )
