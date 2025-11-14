from __future__ import annotations

from datetime import datetime
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

JobState = Literal["pending", "processing", "succeeded", "failed"]


class SourceDescriptor(BaseModel):
    type: Literal["text", "audio", "video", "image", "code", "web", "pdf", "mixed"] = "text"
    uri: Optional[str] = None


class CapsuleMetadata(BaseModel):
    capsule_id: str
    version: str = "1.0.0"
    status: Literal["draft", "active", "archived"] = "active"
    author: str = "system"
    created_at: datetime
    language: str = "en"
    source: SourceDescriptor = SourceDescriptor()
    tags: Annotated[List[str], Field(min_length=3, max_length=10)]
    length: Dict[str, int]
    semantic_hash: str


class CapsuleCorePayload(BaseModel):
    content_type: Literal["text/markdown", "text/plain", "application/json", "code", "other"] = "text/markdown"
    content: str
    truncation_note: Optional[str] = None


class CapsuleNeuroConcentrate(BaseModel):
    summary: Annotated[str, Field(min_length=10)]
    keywords: Annotated[List[str], Field(min_length=5, max_length=12)]
    entities: List[Dict[str, str]]
    claims: List[str]
    insights: List[str]
    questions: List[str]
    archetypes: List[str]
    symbols: List[str]
    emotional_charge: float
    vector_hint: Annotated[List[str], Field(min_length=8, max_length=16)]
    semantic_hash: str


class CapsuleLink(BaseModel):
    rel: Literal[
        "supports",
        "contradicts",
        "extends",
        "duplicates",
        "references",
        "depends_on",
        "derived_from"
    ]
    target_capsule_id: str
    reason: str
    confidence: float


class CapsuleRecursive(BaseModel):
    links: List[CapsuleLink]
    actions: List[Dict[str, object]]
    prompts: List[Dict[str, str]]
    confidence: float


class CapsuleModel(BaseModel):
    include_in_rag: bool = True
    metadata: CapsuleMetadata
    core_payload: CapsuleCorePayload
    neuro_concentrate: CapsuleNeuroConcentrate
    recursive: CapsuleRecursive


class JobErrorIssue(BaseModel):
    path: str
    message: str


class JobError(BaseModel):
    code: int
    stage: str
    issues: List[JobErrorIssue]


class JobModel(BaseModel):
    id: str
    code: int = 100
    stage: str = "queued"
    state: JobState
    progress: int
    created_at: datetime
    updated_at: datetime
    error: Optional[JobError] = None
    capsule_id: Optional[str] = None


class IngestRequest(BaseModel):
    title: str
    content: str
    tags: Annotated[List[str], Field(min_length=1)]
    include_in_rag: bool = True
    author: str = "user"
    language: str = "en"
    source: SourceDescriptor = SourceDescriptor()
    privacy_level: Literal["standard", "high"] = "standard"


class ChatRequest(BaseModel):
    query: str
    scope: List[str] = []  # Can be: ["my"], ["public"], ["inbox"], or ["tag1", "tag2", ...] for tag-based scope


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    metrics: Dict[str, float]


class CapsulePatch(BaseModel):
    """PATCH request model for updating capsules (Section 4: API)."""
    include_in_rag: Optional[bool] = None
    tags: Optional[Annotated[List[str], Field(min_length=3, max_length=10)]] = None
    status: Optional[Literal["draft", "active", "archived"]] = None


class ObservabilityReport(BaseModel):
    name: str
    status: Literal["ok", "warning", "error"]
    details: str
    metrics: Dict[str, float]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Optional[dict] = None  # Component status for detailed health checks
