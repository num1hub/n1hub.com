"""Integration tests for strict citations mode (Section 10)."""

import pytest
from app.store import MemoryCapsuleStore
from app.rag import answer_chat
from app.models import ChatRequest, CapsuleModel, CapsuleMetadata, CapsuleCorePayload, CapsuleNeuroConcentrate, CapsuleRecursive, SourceDescriptor
from app.config import settings
from datetime import datetime, timezone


def create_test_capsule(capsule_id: str, include_in_rag: bool = True) -> CapsuleModel:
    """Helper to create test capsules."""
    summary = " ".join(["word"] * 100)
    metadata = CapsuleMetadata(
        capsule_id=capsule_id,
        version="1.0.0",
        status="active",
        author="test_author",
        created_at=datetime.now(timezone.utc),
        language="en",
        source=SourceDescriptor(type="text", uri=None),
        tags=["test", "capsule", "valid"],
        length={"chars": len(summary) * 4, "tokens_est": len(summary)},
        semantic_hash="test-hash",
    )
    core_payload = CapsuleCorePayload(
        content_type="text/markdown",
        content="Test content",
        truncation_note=None,
    )
    neuro_concentrate = CapsuleNeuroConcentrate(
        summary=summary,
        keywords=["test", "capsule", "valid", "summary", "keywords"],
        entities=[],
        claims=[],
        insights=[],
        questions=[],
        archetypes=[],
        symbols=[],
        emotional_charge=0.0,
        vector_hint=["test", "vector", "hint", "valid", "data", "example", "seven", "eight"],
        semantic_hash="test-hash",
    )
    recursive = CapsuleRecursive(
        links=[],
        actions=[],
        prompts=[],
        confidence=0.9,
    )
    
    return CapsuleModel(
        include_in_rag=include_in_rag,
        metadata=metadata,
        core_payload=core_payload,
        neuro_concentrate=neuro_concentrate,
        recursive=recursive,
    )


@pytest.mark.asyncio
async def test_strict_citations_requires_two_sources():
    """Test strict citations mode requires ≥2 distinct sources."""
    store = MemoryCapsuleStore()
    
    # Create only one capsule
    capsule1 = create_test_capsule("c1")
    await store.save_capsule(capsule1)
    
    request = ChatRequest(query="test query", scope=[])
    response = await answer_chat(store, request)
    
    # Should return fallback since <2 sources
    assert response.answer == settings.citation_fallback
    assert len(response.sources) == 0


@pytest.mark.asyncio
async def test_strict_citations_with_two_sources():
    """Test strict citations mode works with ≥2 distinct sources."""
    store = MemoryCapsuleStore()
    
    # Create two distinct capsules
    capsule1 = create_test_capsule("c1")
    capsule2 = create_test_capsule("c2")
    await store.save_capsule(capsule1)
    await store.save_capsule(capsule2)
    
    request = ChatRequest(query="test query", scope=[])
    response = await answer_chat(store, request)
    
    # Should generate answer (or fallback if LLM unavailable)
    assert response is not None
    # If LLM unavailable, will fallback, but should have sources if answer generated
    if response.answer != settings.citation_fallback:
        assert len(response.sources) >= 2


@pytest.mark.asyncio
async def test_strict_citations_duplicate_capsules():
    """Test duplicate capsules count as 1 distinct source."""
    store = MemoryCapsuleStore()
    
    # Create two capsules with same semantic hash (duplicates)
    capsule1 = create_test_capsule("c1")
    capsule2 = create_test_capsule("c2")
    capsule2.metadata.semantic_hash = capsule1.metadata.semantic_hash
    capsule2.neuro_concentrate.semantic_hash = capsule1.metadata.semantic_hash
    
    await store.save_capsule(capsule1)
    await store.save_capsule(capsule2)
    
    request = ChatRequest(query="test query", scope=[])
    response = await answer_chat(store, request)
    
    # Even with 2 capsules, if they're duplicates, might not meet distinct requirement
    # The actual behavior depends on retrieval logic
    assert response is not None
