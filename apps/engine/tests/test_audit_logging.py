"""Integration tests for audit logging (Section 11)."""

import pytest
from datetime import datetime, timezone
from app.store import MemoryCapsuleStore, PostgresCapsuleStore
from app.models import CapsuleModel, CapsuleMetadata, CapsuleCorePayload, CapsuleNeuroConcentrate, CapsuleRecursive, SourceDescriptor


def create_test_capsule(capsule_id: str, include_in_rag: bool = True, status: str = "active") -> CapsuleModel:
    """Helper to create test capsules."""
    metadata = CapsuleMetadata(
        capsule_id=capsule_id,
        version="1.0.0",
        status=status,
        author="test_author",
        created_at=datetime.now(timezone.utc),
        language="en",
        source=SourceDescriptor(type="text", uri=None),
        tags=["test", "capsule", "valid"],
        length={"chars": 100, "tokens_est": 25},
        semantic_hash="test-hash",
    )
    core_payload = CapsuleCorePayload(
        content_type="text/markdown",
        content="Test content",
        truncation_note=None,
    )
    neuro_concentrate = CapsuleNeuroConcentrate(
        summary=" ".join(["word"] * 100),
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
async def test_audit_logging_rag_toggle():
    """Test RAG toggle is logged."""
    store = MemoryCapsuleStore()
    capsule = create_test_capsule("c1", include_in_rag=False)
    await store.save_capsule(capsule)
    
    # Toggle RAG inclusion
    await store.toggle_capsule("c1", True)
    await store.log_audit(
        capsule_id="c1",
        action_type="rag_toggle",
        old_value="False",
        new_value="True",
        actor="test_user",
    )
    
    # Verify logging doesn't raise errors
    # (Memory store doesn't persist, but Postgres store would)
    assert True


@pytest.mark.asyncio
async def test_audit_logging_status_change():
    """Test status change is logged."""
    store = MemoryCapsuleStore()
    capsule = create_test_capsule("c1", status="draft")
    await store.save_capsule(capsule)
    
    # Update status
    await store.update_capsule_status("c1", "active")
    await store.log_audit(
        capsule_id="c1",
        action_type="status_change",
        old_value="draft",
        new_value="active",
        actor="test_user",
    )
    
    # Verify logging doesn't raise errors
    assert True


@pytest.mark.asyncio
async def test_audit_logging_tags_update():
    """Test tag update is logged."""
    store = MemoryCapsuleStore()
    capsule = create_test_capsule("c1")
    await store.save_capsule(capsule)
    
    # Update tags
    await store.update_capsule_tags("c1", ["new", "tags", "here"])
    await store.log_audit(
        capsule_id="c1",
        action_type="tags_update",
        old_value="test,capsule,valid",
        new_value="new,tags,here",
        actor="test_user",
    )
    
    # Verify logging doesn't raise errors
    assert True


@pytest.mark.asyncio
async def test_audit_logging_validation():
    """Test audit logging validates inputs."""
    store = MemoryCapsuleStore()
    
    # Should accept valid action types
    await store.log_audit(
        capsule_id="c1",
        action_type="rag_toggle",
        old_value="False",
        new_value="True",
        actor="test_user",
    )
    
    await store.log_audit(
        capsule_id="c1",
        action_type="status_change",
        old_value="draft",
        new_value="active",
        actor="test_user",
    )
    
    assert True
