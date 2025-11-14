from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

import asyncpg
from asyncpg import Pool

from .config import settings
from .models import CapsuleModel, ChatRequest, JobModel, JobError, JobErrorIssue
from .store import BaseCapsuleStore


class PostgresCapsuleStore(BaseCapsuleStore):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: Optional[Pool] = None

    async def _get_pool(self) -> Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)
        return self._pool

    async def create_job(self) -> JobModel:
        from ulid import ULID
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            job_id = str(ULID())
            now = datetime.now(timezone.utc)
            await conn.execute(
                "INSERT INTO jobs (id, state, code, stage, progress, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                job_id,
                "pending",
                100,
                "queued",
                0,
                now,
                now,
            )
            return JobModel(
                id=job_id,
                code=100,
                stage="queued",
                state="pending",
                progress=0,
                created_at=now,
                updated_at=now,
            )

    async def update_job(
        self,
        job_id: str,
        *,
        code: Optional[int] = None,
        stage: Optional[str] = None,
        state: Optional[str] = None,
        progress: Optional[int] = None,
        error: Optional[dict] = None,
        capsule_id: Optional[str] = None,
    ) -> JobModel:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            updates: List[str] = []
            params: List[object] = []
            param_idx = 1

            if code is not None:
                updates.append(f"code = ${param_idx}")
                params.append(code)
                param_idx += 1
            if stage is not None:
                updates.append(f"stage = ${param_idx}")
                params.append(stage)
                param_idx += 1
            if state is not None:
                updates.append(f"state = ${param_idx}")
                params.append(state)
                param_idx += 1
            if progress is not None:
                updates.append(f"progress = ${param_idx}")
                params.append(progress)
                param_idx += 1
            if error is not None:
                updates.append(f"error = ${param_idx}")
                params.append(json.dumps(error))
                param_idx += 1
            if capsule_id is not None:
                # Note: jobs table doesn't have capsule_id column in schema, but we'll handle it in payload
                pass

            updates.append(f"updated_at = ${param_idx}")
            params.append(datetime.now(timezone.utc))
            param_idx += 1

            params.append(job_id)

            await conn.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE id = ${param_idx}",
                *params,
            )

            row = await conn.fetchrow(
                "SELECT id, code, stage, state, progress, error, created_at, updated_at FROM jobs WHERE id = $1",
                job_id,
            )
            if not row:
                raise KeyError(f"Job {job_id} not found")

            error_obj = None
            if row["error"]:
                error_data = json.loads(row["error"]) if isinstance(row["error"], str) else row["error"]
                if isinstance(error_data, dict) and "code" in error_data:
                    error_obj = JobError(
                        code=error_data["code"],
                        stage=error_data["stage"],
                        issues=[JobErrorIssue(**issue) for issue in error_data.get("issues", [])],
                    )

            return JobModel(
                id=row["id"],
                code=row["code"],
                stage=row["stage"],
                state=row["state"],  # type: ignore[assignment]
                progress=row["progress"],
                error=error_obj,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def save_capsule(self, capsule: CapsuleModel) -> CapsuleModel:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            payload = {
                "metadata": capsule.metadata.model_dump(),
                "core_payload": capsule.core_payload.model_dump(),
                "neuro_concentrate": capsule.neuro_concentrate.model_dump(),
                "recursive": capsule.recursive.model_dump(),
            }
            await conn.execute(
                """
                INSERT INTO capsules (id, version, status, author, created_at, language, semantic_hash, include_in_rag, payload)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    version = EXCLUDED.version,
                    status = EXCLUDED.status,
                    semantic_hash = EXCLUDED.semantic_hash,
                    include_in_rag = EXCLUDED.include_in_rag,
                    payload = EXCLUDED.payload
                """,
                capsule.metadata.capsule_id,
                capsule.metadata.version,
                capsule.metadata.status,
                capsule.metadata.author,
                capsule.metadata.created_at,
                capsule.metadata.language,
                capsule.metadata.semantic_hash,
                capsule.include_in_rag,
                json.dumps(payload),
            )
            return capsule

    async def list_jobs(self) -> List[JobModel]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, code, stage, state, progress, error, created_at, updated_at FROM jobs ORDER BY created_at DESC"
            )
            jobs: List[JobModel] = []
            for row in rows:
                error_obj = None
                if row["error"]:
                    error_data = json.loads(row["error"]) if isinstance(row["error"], str) else row["error"]
                    if isinstance(error_data, dict) and "code" in error_data:
                        error_obj = JobError(
                            code=error_data["code"],
                            stage=error_data["stage"],
                            issues=[JobErrorIssue(**issue) for issue in error_data.get("issues", [])],
                        )
                jobs.append(
                    JobModel(
                        id=row["id"],
                        code=row["code"],
                        stage=row["stage"],
                        state=row["state"],  # type: ignore[assignment]
                        progress=row["progress"],
                        error=error_obj,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                )
            return jobs

    async def get_job(self, job_id: str) -> JobModel:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, code, stage, state, progress, error, created_at, updated_at FROM jobs WHERE id = $1",
                job_id,
            )
            if not row:
                raise KeyError(f"Job {job_id} not found")

            error_obj = None
            if row["error"]:
                error_data = json.loads(row["error"]) if isinstance(row["error"], str) else row["error"]
                if isinstance(error_data, dict) and "code" in error_data:
                    error_obj = JobError(
                        code=error_data["code"],
                        stage=error_data["stage"],
                        issues=[JobErrorIssue(**issue) for issue in error_data.get("issues", [])],
                    )

            return JobModel(
                id=row["id"],
                code=row["code"],
                stage=row["stage"],
                state=row["state"],  # type: ignore[assignment]
                progress=row["progress"],
                error=error_obj,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_capsules(self, include_in_rag: Optional[bool] = None) -> List[CapsuleModel]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            query = "SELECT payload, include_in_rag FROM capsules"
            params: List[object] = []
            if include_in_rag is not None:
                query += " WHERE include_in_rag = $1"
                params.append(include_in_rag)
            rows = await conn.fetch(query, *params)
            capsules: List[CapsuleModel] = []
            for row in rows:
                payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
                from .models import (
                    CapsuleCorePayload,
                    CapsuleMetadata,
                    CapsuleNeuroConcentrate,
                    CapsuleRecursive,
                )

                capsule = CapsuleModel(
                    include_in_rag=row["include_in_rag"],
                    metadata=CapsuleMetadata(**payload["metadata"]),
                    core_payload=CapsuleCorePayload(**payload["core_payload"]),
                    neuro_concentrate=CapsuleNeuroConcentrate(**payload["neuro_concentrate"]),
                    recursive=CapsuleRecursive(**payload["recursive"]),
                )
                capsules.append(capsule)
            return capsules

    async def get_capsule(self, capsule_id: str) -> CapsuleModel:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT payload, include_in_rag FROM capsules WHERE id = $1", capsule_id)
            if not row:
                raise KeyError(f"Capsule {capsule_id} not found")

            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
            from .models import (
                CapsuleCorePayload,
                CapsuleMetadata,
                CapsuleNeuroConcentrate,
                CapsuleRecursive,
            )

            return CapsuleModel(
                include_in_rag=row["include_in_rag"],
                metadata=CapsuleMetadata(**payload["metadata"]),
                core_payload=CapsuleCorePayload(**payload["core_payload"]),
                neuro_concentrate=CapsuleNeuroConcentrate(**payload["neuro_concentrate"]),
                recursive=CapsuleRecursive(**payload["recursive"]),
            )

    async def toggle_capsule(self, capsule_id: str, include_in_rag: bool) -> CapsuleModel:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("UPDATE capsules SET include_in_rag = $1 WHERE id = $2", include_in_rag, capsule_id)
            return await self.get_capsule(capsule_id)

    async def update_capsule_tags(self, capsule_id: str, tags: List[str]) -> CapsuleModel:
        """Update capsule tags (validates 3-10 items, lowercase, no PII)."""
        import json
        from .utils.pii import contains_pii_in_metadata_field
        
        # Validate and normalize tags
        normalized_tags = [tag.lower().strip() for tag in tags if tag.strip()]
        if len(normalized_tags) < 3 or len(normalized_tags) > 10:
            raise ValueError(f"Tags must be 3-10 items, got {len(normalized_tags)}")
        # Check for PII
        if contains_pii_in_metadata_field(normalized_tags):
            raise ValueError("Tags contain PII - remove personal identifiers before updating")
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Update tags in payload JSONB
            capsule = await self.get_capsule(capsule_id)
            capsule.metadata.tags = normalized_tags
            # Save updated capsule
            await self.save_capsule(capsule)
            return capsule

    async def update_capsule_status(self, capsule_id: str, status: str) -> CapsuleModel:
        """Update capsule status."""
        if status not in ["draft", "active", "archived"]:
            raise ValueError(f"Invalid status: {status}")
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Update status in payload JSONB
            capsule = await self.get_capsule(capsule_id)
            capsule.metadata.status = status
            # Save updated capsule
            await self.save_capsule(capsule)
            return capsule

    async def record_artifact(self, job_id: str, artifact: dict) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO artifacts (job_id, kind, uri, expires_at) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                job_id,
                artifact.get("kind"),
                artifact.get("uri"),
                artifact.get("expires_at"),
            )

    async def list_artifacts(self, job_id: str) -> List[dict]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT kind, uri, expires_at FROM artifacts WHERE job_id = $1", job_id)
            return [{"kind": r["kind"], "uri": r["uri"], "expires_at": r["expires_at"]} for r in rows]

    async def search(self, chat: ChatRequest, top_k: int) -> List[CapsuleModel]:
        # Lexical fallback
        all_capsules = await self.list_capsules()
        scope = set(tag.lower() for tag in chat.scope)
        scored: List[tuple[float, CapsuleModel]] = []
        for capsule in all_capsules:
            if scope and not scope.intersection(tag.lower() for tag in capsule.metadata.tags):
                continue
            text = " ".join([
                capsule.neuro_concentrate.summary,
                " ".join(capsule.neuro_concentrate.keywords),
                capsule.core_payload.content
            ]).lower()
            score = sum(text.count(token) for token in chat.query.lower().split())
            score += 2 if capsule.include_in_rag else -1
            scored.append((score, capsule))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [capsule for (_score, capsule) in scored[:top_k] if _score > 0]

    async def save_vector(self, capsule_id: str, embedding: List[float]) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Convert to pgvector format: array literal
            embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"
            await conn.execute(
                """
                INSERT INTO capsule_vectors (capsule_id, embedding, method)
                VALUES ($1, $2::vector, $3)
                ON CONFLICT (capsule_id) DO UPDATE SET embedding = EXCLUDED.embedding
                """,
                capsule_id,
                embedding_str,
                "hnsw",
            )

    async def vector_search(self, query_embedding: List[float], top_k: int, scope: Optional[List[str]] = None) -> List[tuple[CapsuleModel, float]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Convert embedding to pgvector format
            embedding_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
            query = """
                SELECT c.payload, c.include_in_rag, 1 - (cv.embedding <=> $1::vector) as similarity
                FROM capsules c
                JOIN capsule_vectors cv ON c.id = cv.capsule_id
            """
            params: List[object] = [embedding_str]
            param_idx = 2
            if scope:
                query += f" WHERE c.id = ANY(${param_idx}::text[])"
                params.append(scope)
                param_idx += 1
            query += f" ORDER BY cv.embedding <=> $1::vector LIMIT ${param_idx}"
            params.append(top_k)

            rows = await conn.fetch(query, *params)
            results: List[tuple[CapsuleModel, float]] = []
            for row in rows:
                payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
                from .models import (
                    CapsuleCorePayload,
                    CapsuleMetadata,
                    CapsuleNeuroConcentrate,
                    CapsuleRecursive,
                )

                capsule = CapsuleModel(
                    include_in_rag=row["include_in_rag"],
                    metadata=CapsuleMetadata(**payload["metadata"]),
                    core_payload=CapsuleCorePayload(**payload["core_payload"]),
                    neuro_concentrate=CapsuleNeuroConcentrate(**payload["neuro_concentrate"]),
                    recursive=CapsuleRecursive(**payload["recursive"]),
                )
                results.append((capsule, float(row["similarity"])))
            return results

    async def bootstrap(self, capsules: List[CapsuleModel]) -> None:
        from .vectorizer import get_vectorizer
        vectorizer = get_vectorizer()
        for capsule in capsules:
            await self.save_capsule(capsule)
            # Generate semantic embedding
            text = f"{capsule.neuro_concentrate.summary} {' '.join(capsule.neuro_concentrate.keywords)}"
            embedding = vectorizer.embed(text)
            await self.save_vector(capsule.metadata.capsule_id, embedding)

    async def log_audit(
        self,
        capsule_id: str,
        action_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        actor: str = "system",
        metadata: Optional[dict] = None,
    ) -> None:
        """Log audit event to audit_logs table (Section 11: Security & Privacy Defaults)."""
        import json
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_logs (capsule_id, action_type, old_value, new_value, actor, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                capsule_id,
                action_type,
                old_value,
                new_value,
                actor,
                json.dumps(metadata) if metadata else None,
            )
