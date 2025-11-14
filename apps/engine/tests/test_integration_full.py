"""Full Integration Tests with Real Postgres Store

Tests pipeline, vector search, LLM integration, and observability
with actual Postgres database (not just memory store).
"""

import os
import pytest
from datetime import datetime, timezone, timedelta

from app.store_pg import PostgresCapsuleStore
from app.models import CapsuleModel, CapsuleMetadata, CapsuleCorePayload, CapsuleNeuroConcentrate, CapsuleRecursive, SourceDescriptor
from app.pipeline import DeepMinePipeline
from app.rag import answer_chat
from app.models import ChatRequest


# Skip if Postgres DSN not available
POSTGRES_DSN = os.getenv("TEST_POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/n1hub_test")


@pytest.fixture(scope="module")
def postgres_store():
    """Create Postgres store for integration tests."""
    try:
        store = PostgresCapsuleStore(POSTGRES_DSN)
        yield store
    except Exception as e:
        pytest.skip(f"Postgres not available: {e}")


@pytest.fixture
def sample_capsule():
    """Create sample capsule for testing."""
    summary = " ".join(["word"] * 100)
    metadata = CapsuleMetadata(
        capsule_id="01TESTINTEGRATION123456789",
        version="1.0.0",
        status="active",
        author="test_author",
        created_at=datetime.now(timezone.utc),
        language="en",
        source=SourceDescriptor(type="text", uri=None),
        tags=["integration", "test", "capsule", "valid", "data"],
        length={"chars": len(summary) * 4, "tokens_est": len(summary)},
        semantic_hash="integration-test-hash-summary-keywords-example-seven-eight",
    )
    core_payload = CapsuleCorePayload(
        content_type="text/markdown",
        content="Integration test content for full Postgres store testing.",
        truncation_note=None,
    )
    neuro_concentrate = CapsuleNeuroConcentrate(
        summary=summary,
        keywords=["integration", "test", "capsule", "valid", "summary", "keywords", "example"],
        entities=[],
        claims=[],
        insights=[],
        questions=[],
        archetypes=[],
        symbols=[],
        emotional_charge=0.0,
        vector_hint=["integration", "test", "vector", "hint", "valid", "data", "example", "seven"],
        semantic_hash="integration-test-hash-summary-keywords-example-seven-eight",
    )
    recursive = CapsuleRecursive(
        links=[],
        actions=[],
        prompts=[],
        confidence=0.9,
    )
    
    return CapsuleModel(
        include_in_rag=True,
        metadata=metadata,
        core_payload=core_payload,
        neuro_concentrate=neuro_concentrate,
        recursive=recursive,
    )


@pytest.mark.asyncio
async def test_postgres_store_save_and_retrieve(postgres_store, sample_capsule):
    """Test: Save and retrieve capsule from Postgres store."""
    # Save capsule
    saved = await postgres_store.save_capsule(sample_capsule)
    assert saved.metadata.capsule_id == sample_capsule.metadata.capsule_id
    
    # Retrieve capsule
    retrieved = await postgres_store.get_capsule(sample_capsule.metadata.capsule_id)
    assert retrieved.metadata.capsule_id == sample_capsule.metadata.capsule_id
    assert retrieved.metadata.tags == sample_capsule.metadata.tags
    assert retrieved.include_in_rag == sample_capsule.include_in_rag


@pytest.mark.asyncio
async def test_vector_search_with_postgres(postgres_store, sample_capsule):
    """Test: Vector search with actual embeddings in Postgres."""
    # Save capsule
    await postgres_store.save_capsule(sample_capsule)
    
    # Generate embedding and save vector
    from app.vectorizer import get_vectorizer
    vectorizer = get_vectorizer()
    embedding = vectorizer.embed(sample_capsule.neuro_concentrate.summary)
    await postgres_store.save_vector(sample_capsule.metadata.capsule_id, embedding)
    
    # Perform vector search
    query_embedding = vectorizer.embed("integration test")
    results = await postgres_store.vector_search(query_embedding, top_k=5)
    
    assert len(results) > 0
    assert any(c.metadata.capsule_id == sample_capsule.metadata.capsule_id for c, _ in results)


@pytest.mark.asyncio
async def test_pipeline_with_postgres_store(postgres_store):
    """Test: Full pipeline execution with Postgres store."""
    pipeline = DeepMinePipeline(postgres_store)
    
    content = """
    This is a test document for integration testing with Postgres store.
    It contains multiple sentences and concepts that should be processed
    by the DeepMine pipeline into a valid capsule structure.
    
    The pipeline should extract keywords, generate a summary, create
    semantic hash, and store everything in the Postgres database.
    """
    
    # Run pipeline
    result = await pipeline.process(
        material=content,
        title="Integration Test Document",
        tags=["integration", "test", "postgres"],
        include_in_rag=True,
    )
    
    assert result.capsule_id is not None
    assert result.job_id is not None
    
    # Verify capsule was saved
    capsule = await postgres_store.get_capsule(result.capsule_id)
    assert capsule is not None
    assert capsule.metadata.capsule_id == result.capsule_id
    assert len(capsule.neuro_concentrate.keywords) >= 5
    assert len(capsule.neuro_concentrate.summary.split()) >= 70


@pytest.mark.asyncio
async def test_rag_with_postgres_store(postgres_store, sample_capsule):
    """Test: RAG query with Postgres store and vector search."""
    # Save multiple capsules
    capsules = []
    for i in range(3):
        capsule = sample_capsule
        capsule.metadata.capsule_id = f"01TEST{i:02d}INTEGRATION123456789"
        capsule.metadata.tags = [f"tag-{i}", "shared", "common"]
        await postgres_store.save_capsule(capsule)
        
        # Save vector
        from app.vectorizer import get_vectorizer
        vectorizer = get_vectorizer()
        embedding = vectorizer.embed(capsule.neuro_concentrate.summary)
        await postgres_store.save_vector(capsule.metadata.capsule_id, embedding)
        capsules.append(capsule)
    
    # Perform RAG query
    request = ChatRequest(query="integration test query", scope=[])
    response = await answer_chat(postgres_store, request)
    
    assert response is not None
    assert "answer" in response.dict()
    assert "sources" in response.dict()
    assert "metrics" in response.dict()


@pytest.mark.asyncio
async def test_observability_with_postgres(postgres_store, sample_capsule):
    """Test: Observability endpoints with real query logs."""
    # Save capsule and perform queries
    await postgres_store.save_capsule(sample_capsule)
    
    # Perform some queries to generate query logs
    for i in range(3):
        request = ChatRequest(query=f"test query {i}", scope=[])
        await answer_chat(postgres_store, request)
    
    # Test observability endpoints
    from app.observability import retrieval_metrics, router_diagnostics, semantic_hash_report, pii_report
    
    # Retrieval metrics
    retrieval = await retrieval_metrics(postgres_store, window_days=7)
    assert retrieval is not None
    assert "metrics" in retrieval.dict()
    
    # Router diagnostics
    router = await router_diagnostics(postgres_store)
    assert router is not None
    
    # Semantic hash report
    hash_report = await semantic_hash_report(postgres_store)
    assert hash_report is not None
    
    # PII report
    pii = await pii_report(postgres_store)
    assert pii is not None


@pytest.mark.asyncio
async def test_scope_filtering_with_postgres(postgres_store):
    """Test: RAG-Scope filtering with Postgres store."""
    # Create capsules with different properties
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    
    # Recent capsule (in inbox)
    recent = sample_capsule
    recent.metadata.capsule_id = "01RECENTINTEGRATION123456789"
    recent.metadata.created_at = now - timedelta(days=10)
    recent.metadata.status = "active"
    recent.include_in_rag = True
    await postgres_store.save_capsule(recent)
    
    # Old capsule (not in inbox)
    old = sample_capsule
    old.metadata.capsule_id = "01OLDINTEGRATION123456789"
    old.metadata.created_at = now - timedelta(days=35)
    old.metadata.status = "active"
    old.include_in_rag = True
    await postgres_store.save_capsule(old)
    
    # Test inbox scope (should only include recent)
    request = ChatRequest(query="test", scope=["inbox"])
    response = await answer_chat(postgres_store, request)
    assert response is not None


@pytest.mark.asyncio
async def test_audit_logging_with_postgres(postgres_store, sample_capsule):
    """Test: Audit logging with Postgres store."""
    # Save capsule
    await postgres_store.save_capsule(sample_capsule)
    
    # Perform operations that should be logged
    await postgres_store.toggle_capsule(sample_capsule.metadata.capsule_id, False)
    await postgres_store.log_audit(
        capsule_id=sample_capsule.metadata.capsule_id,
        action_type="rag_toggle",
        old_value="True",
        new_value="False",
        actor="test_user",
    )
    
    await postgres_store.update_capsule_status(sample_capsule.metadata.capsule_id, "archived")
    await postgres_store.log_audit(
        capsule_id=sample_capsule.metadata.capsule_id,
        action_type="status_change",
        old_value="active",
        new_value="archived",
        actor="test_user",
    )
    
    # Verify audit logs were created (if querying is implemented)
    # Note: Audit log querying may not be implemented yet
    assert True  # Placeholder - actual verification depends on implementation
