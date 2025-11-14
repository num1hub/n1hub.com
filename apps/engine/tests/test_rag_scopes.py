"""Integration tests for RAG-Scope profiles (Section 10)."""

import asyncio
from datetime import datetime, timezone, timedelta

from app.store import MemoryCapsuleStore
from app.rag import answer_chat, _parse_scope, _filter_by_scope_type
from app.models import ChatRequest, CapsuleModel, CapsuleMetadata, CapsuleCorePayload, CapsuleNeuroConcentrate, CapsuleRecursive, SourceDescriptor


def create_test_capsule(
    capsule_id: str,
    tags: list[str] = ["test", "capsule", "valid"],
    include_in_rag: bool = True,
    status: str = "active",
    created_days_ago: int = 0,
) -> CapsuleModel:
    """Helper to create test capsules."""
    created_at = datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    summary = " ".join(["word"] * 100)  # 100 words
    
    metadata = CapsuleMetadata(
        capsule_id=capsule_id,
        version="1.0.0",
        status=status,
        author="test_author",
        created_at=created_at,
        language="en",
        source=SourceDescriptor(type="text", uri=None),
        tags=tags,
        length={"chars": len(summary) * 4, "tokens_est": len(summary)},
        semantic_hash="test-hash-summary-keywords-example-seven-eight",
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
        semantic_hash="test-hash-summary-keywords-example-seven-eight",
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


def test_parse_scope_defaults_to_my():
    """Test empty scope defaults to 'my'."""
    scope_type, tags = _parse_scope([])
    assert scope_type == "my"
    assert tags == []


def test_parse_scope_types():
    """Test scope type parsing."""
    assert _parse_scope(["my"]) == ("my", [])
    assert _parse_scope(["public"]) == ("public", [])
    assert _parse_scope(["inbox"]) == ("inbox", [])
    assert _parse_scope(["tag1", "tag2"]) == ("tags", ["tag1", "tag2"])


def test_filter_by_scope_type_my():
    """Test 'my' scope filters active capsules with include_in_rag=true."""
    capsules = [
        create_test_capsule("c1", include_in_rag=True, status="active"),
        create_test_capsule("c2", include_in_rag=False, status="active"),
        create_test_capsule("c3", include_in_rag=True, status="draft"),
    ]
    filtered = _filter_by_scope_type(capsules, "my")
    assert len(filtered) == 1
    assert filtered[0].metadata.capsule_id == "c1"


def test_filter_by_scope_type_inbox():
    """Test 'inbox' scope filters by last 30 days."""
    capsules = [
        create_test_capsule("c1", created_days_ago=10, include_in_rag=True, status="active"),
        create_test_capsule("c2", created_days_ago=35, include_in_rag=True, status="active"),
        create_test_capsule("c3", created_days_ago=5, include_in_rag=True, status="active"),
    ]
    filtered = _filter_by_scope_type(capsules, "inbox")
    assert len(filtered) == 2
    assert "c1" in [c.metadata.capsule_id for c in filtered]
    assert "c3" in [c.metadata.capsule_id for c in filtered]
    assert "c2" not in [c.metadata.capsule_id for c in filtered]


def test_filter_by_scope_type_public():
    """Test 'public' scope filters active capsules."""
    capsules = [
        create_test_capsule("c1", include_in_rag=True, status="active"),
        create_test_capsule("c2", include_in_rag=True, status="draft"),
        create_test_capsule("c3", include_in_rag=True, status="archived"),
    ]
    filtered = _filter_by_scope_type(capsules, "public")
    assert len(filtered) == 1
    assert filtered[0].metadata.capsule_id == "c1"


def test_filter_by_scope_type_tags():
    """Test 'tags' scope doesn't filter (tags handled in search)."""
    capsules = [
        create_test_capsule("c1", tags=["tag1", "alpha", "beta"], include_in_rag=True),
        create_test_capsule("c2", tags=["tag2", "gamma", "delta"], include_in_rag=True),
    ]
    filtered = _filter_by_scope_type(capsules, "tags")
    assert len(filtered) == 2  # All included, tag filtering happens in search


def test_answer_chat_with_my_scope():
    """Test chat with 'my' scope."""

    async def _run() -> None:
        store = MemoryCapsuleStore()
        capsule1 = create_test_capsule("c1", include_in_rag=True, status="active")
        capsule2 = create_test_capsule("c2", include_in_rag=False, status="active")  # Should be excluded
        await store.save_capsule(capsule1)
        await store.save_capsule(capsule2)

        request = ChatRequest(query="test query", scope=["my"])
        response = await answer_chat(store, request)

        assert response is not None

    asyncio.run(_run())
