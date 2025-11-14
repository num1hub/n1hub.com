from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ulid import ULID

from .models import CapsuleModel, ChatRequest, JobModel


class BaseCapsuleStore(ABC):
    @abstractmethod
    async def create_job(self) -> JobModel:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def save_capsule(self, capsule: CapsuleModel) -> CapsuleModel:
        ...

    @abstractmethod
    async def list_jobs(self) -> List[JobModel]:
        ...

    @abstractmethod
    async def get_job(self, job_id: str) -> JobModel:
        ...

    @abstractmethod
    async def list_capsules(self, include_in_rag: Optional[bool] = None) -> List[CapsuleModel]:
        ...

    @abstractmethod
    async def get_capsule(self, capsule_id: str) -> CapsuleModel:
        ...

    @abstractmethod
    async def toggle_capsule(self, capsule_id: str, include_in_rag: bool) -> CapsuleModel:
        ...

    @abstractmethod
    async def update_capsule_tags(self, capsule_id: str, tags: List[str]) -> CapsuleModel:
        """Update capsule tags (3-10 items, lowercase, no PII)."""
        ...

    @abstractmethod
    async def update_capsule_status(self, capsule_id: str, status: str) -> CapsuleModel:
        """Update capsule status (draft, active, archived)."""
        ...

    @abstractmethod
    async def record_artifact(self, job_id: str, artifact: dict) -> None:
        ...

    @abstractmethod
    async def list_artifacts(self, job_id: str) -> List[dict]:
        ...

    @abstractmethod
    async def search(self, chat: ChatRequest, top_k: int) -> List[CapsuleModel]:
        ...

    @abstractmethod
    async def save_vector(self, capsule_id: str, embedding: List[float]) -> None:
        ...

    @abstractmethod
    async def vector_search(self, query_embedding: List[float], top_k: int, scope: Optional[List[str]] = None) -> List[tuple[CapsuleModel, float]]:
        ...

    @abstractmethod
    async def bootstrap(self, capsules: List[CapsuleModel]) -> None:
        ...

    @abstractmethod
    async def log_audit(
        self,
        capsule_id: str,
        action_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        actor: str = "system",
        metadata: Optional[dict] = None,
    ) -> None:
        """Log audit event for capsule changes (status changes, RAG toggles)."""
        ...


class MemoryCapsuleStore(BaseCapsuleStore):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._capsules: Dict[str, CapsuleModel] = {}
        self._jobs: Dict[str, JobModel] = {}
        self._artifacts: Dict[str, List[dict]] = {}

    async def create_job(self) -> JobModel:
        async with self._lock:
            job_id = str(ULID())
            now = datetime.now(timezone.utc)
            job = JobModel(id=job_id, code=100, stage="queued", state="pending", progress=0, created_at=now, updated_at=now)
            self._jobs[job_id] = job
            return job

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
        async with self._lock:
            job = self._jobs[job_id]
            if code is not None:
                job.code = code
            if stage is not None:
                job.stage = stage
            if state:
                job.state = state  # type: ignore[assignment]
            if progress is not None:
                job.progress = progress
            if error is not None:
                job.error = error
            if capsule_id:
                job.capsule_id = capsule_id
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            return job

    async def save_capsule(self, capsule: CapsuleModel) -> CapsuleModel:
        async with self._lock:
            self._capsules[capsule.metadata.capsule_id] = capsule
            return capsule

    async def list_jobs(self) -> List[JobModel]:
        async with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    async def get_job(self, job_id: str) -> JobModel:
        async with self._lock:
            return self._jobs[job_id]

    async def list_capsules(self, include_in_rag: Optional[bool] = None) -> List[CapsuleModel]:
        async with self._lock:
            capsules = list(self._capsules.values())
        if include_in_rag is None:
            return capsules
        return [capsule for capsule in capsules if capsule.include_in_rag == include_in_rag]

    async def get_capsule(self, capsule_id: str) -> CapsuleModel:
        async with self._lock:
            return self._capsules[capsule_id]

    async def toggle_capsule(self, capsule_id: str, include_in_rag: bool) -> CapsuleModel:
        async with self._lock:
            capsule = self._capsules[capsule_id]
            capsule.include_in_rag = include_in_rag
            self._capsules[capsule_id] = capsule
            return capsule

    async def update_capsule_tags(self, capsule_id: str, tags: List[str]) -> CapsuleModel:
        """Update capsule tags (validates 3-10 items, lowercase, no PII)."""
        from .utils.pii import contains_pii_in_metadata_field
        
        async with self._lock:
            capsule = self._capsules[capsule_id]
            # Validate and normalize tags
            normalized_tags = [tag.lower().strip() for tag in tags if tag.strip()]
            if len(normalized_tags) < 3 or len(normalized_tags) > 10:
                raise ValueError(f"Tags must be 3-10 items, got {len(normalized_tags)}")
            # Check for PII
            if contains_pii_in_metadata_field(normalized_tags):
                raise ValueError("Tags contain PII - remove personal identifiers before updating")
            capsule.metadata.tags = normalized_tags
            self._capsules[capsule_id] = capsule
            return capsule

    async def update_capsule_status(self, capsule_id: str, status: str) -> CapsuleModel:
        """Update capsule status."""
        async with self._lock:
            capsule = self._capsules[capsule_id]
            if status not in ["draft", "active", "archived"]:
                raise ValueError(f"Invalid status: {status}")
            capsule.metadata.status = status
            self._capsules[capsule_id] = capsule
            return capsule

    async def record_artifact(self, job_id: str, artifact: dict) -> None:
        async with self._lock:
            self._artifacts.setdefault(job_id, []).append(artifact)

    async def list_artifacts(self, job_id: str) -> List[dict]:
        async with self._lock:
            return self._artifacts.get(job_id, [])

    async def search(self, chat: ChatRequest, top_k: int) -> List[CapsuleModel]:
        scope = set(tag.lower() for tag in chat.scope)
        async with self._lock:
            capsules = list(self._capsules.values())
        scored: List[tuple[float, CapsuleModel]] = []
        for capsule in capsules:
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
        # Memory store doesn't persist vectors
        pass

    async def vector_search(self, query_embedding: List[float], top_k: int, scope: Optional[List[str]] = None) -> List[tuple[CapsuleModel, float]]:
        # Memory store falls back to lexical search
        return []

    async def bootstrap(self, capsules: List[CapsuleModel]) -> None:
        async with self._lock:
            for capsule in capsules:
                self._capsules[capsule.metadata.capsule_id] = capsule

    async def log_audit(
        self,
        capsule_id: str,
        action_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        actor: str = "system",
        metadata: Optional[dict] = None,
    ) -> None:
        """Log audit event (in-memory store keeps audit logs in memory)."""
        # In-memory store: could store in a list, but for v0.1 we'll just pass through
        # Real implementation would be in Postgres store
        pass


store = MemoryCapsuleStore()
