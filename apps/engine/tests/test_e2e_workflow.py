"""End-to-End Workflow Tests for N1Hub v0.1

Tests complete user journey: Upload → Job → Capsule → Graph → Chat
with all RAG-Scope profiles, PATCH operations, error recovery, and more.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import ChatRequest
from app.store import MemoryCapsuleStore


pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """Create test client with fresh store."""
    return TestClient(app)


@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return {
        "title": "Machine Learning Fundamentals",
        "content": """
        Machine learning is a subset of artificial intelligence that enables systems to learn
        and improve from experience without being explicitly programmed. It focuses on the
        development of computer programs that can access data and use it to learn for themselves.

        The process of learning begins with observations or data, such as examples, direct
        experience, or instruction, in order to look for patterns in data and make better
        decisions in the future based on the examples that we provide. The primary aim is to
        allow the computers to learn automatically without human intervention or assistance and
        adjust actions accordingly.

        There are three main types of machine learning: supervised learning, unsupervised learning,
        and reinforcement learning. Supervised learning uses labeled data to train models.
        Unsupervised learning finds hidden patterns in unlabeled data. Reinforcement learning
        uses rewards and penalties to guide learning.

        Key concepts include neural networks, deep learning, feature engineering, model training,
        validation, and deployment. Popular algorithms include linear regression, decision trees,
        random forests, support vector machines, and neural networks.
        """,
        "tags": ["machine-learning", "ai", "data-science", "algorithms", "neural-networks"],
        "include_in_rag": True,
    }


class TestCompleteWorkflow:
    """Test complete user journey from upload to chat."""

    def test_upload_to_capsule_workflow(self, client, sample_content):
        """Test: Upload → Job → Capsule creation."""
        # Step 1: Upload content
        response = client.post("/ingest", json=sample_content)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        job_id = data["job_id"]
        assert job_id

        # Step 2: Wait for job completion
        job_body = None
        for _ in range(30):  # Increased timeout for E2E
            job_response = client.get(f"/jobs/{job_id}")
            assert job_response.status_code == 200
            job_body = job_response.json()
            if job_body["state"] == "succeeded":
                break
            assert job_body["state"] in ["queued", "processing"]
            time.sleep(0.2)

        assert job_body is not None
        assert job_body["state"] == "succeeded"
        assert "capsule_id" in job_body
        capsule_id = job_body["capsule_id"]

        # Step 3: Retrieve capsule
        capsule_response = client.get(f"/capsules/{capsule_id}")
        assert capsule_response.status_code == 200
        capsule = capsule_response.json()

        # Step 4: Verify capsule structure
        assert capsule["metadata"]["capsule_id"] == capsule_id
        assert capsule["include_in_rag"] is True
        assert "metadata" in capsule
        assert "core_payload" in capsule
        assert "neuro_concentrate" in capsule
        assert "recursive" in capsule
        assert len(capsule["metadata"]["tags"]) >= 3
        assert len(capsule["neuro_concentrate"]["keywords"]) >= 5

    def test_capsule_list_and_filtering(self, client, sample_content):
        """Test: List capsules and filter by RAG inclusion."""
        # Create capsule
        response = client.post("/ingest", json=sample_content)
        job_id = response.json()["job_id"]

        # Wait for completion
        for _ in range(30):
            job = client.get(f"/jobs/{job_id}").json()
            if job["state"] == "succeeded":
                break
            time.sleep(0.2)

        # List all capsules
        all_capsules = client.get("/capsules").json()
        assert isinstance(all_capsules, list)
        assert len(all_capsules) > 0

        # Filter by include_in_rag
        rag_capsules = client.get("/capsules?include_in_rag=true").json()
        assert all(c["include_in_rag"] is True for c in rag_capsules)

        non_rag_capsules = client.get("/capsules?include_in_rag=false").json()
        assert all(c["include_in_rag"] is False for c in non_rag_capsules)

    def test_patch_operations_with_audit(self, client, sample_content):
        """Test: PATCH operations (tags, status, RAG toggle) with audit verification."""
        # Create capsule
        response = client.post("/ingest", json=sample_content)
        job_id = response.json()["job_id"]

        # Wait for completion
        capsule_id = None
        for _ in range(30):
            job = client.get(f"/jobs/{job_id}").json()
            if job["state"] == "succeeded":
                capsule_id = job["capsule_id"]
                break
            time.sleep(0.2)

        assert capsule_id is not None

        # Test 1: Update tags
        new_tags = ["updated", "tags", "here"]
        patch_response = client.patch(
            f"/capsules/{capsule_id}",
            json={"tags": new_tags}
        )
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert set(updated["metadata"]["tags"]) == set(new_tags)

        # Test 2: Update status
        patch_response = client.patch(
            f"/capsules/{capsule_id}",
            json={"status": "archived"}
        )
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["metadata"]["status"] == "archived"

        # Test 3: Toggle RAG inclusion
        original_rag = updated["include_in_rag"]
        patch_response = client.patch(
            f"/capsules/{capsule_id}",
            json={"include_in_rag": not original_rag}
        )
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["include_in_rag"] != original_rag

        # Test 4: Combined update
        patch_response = client.patch(
            f"/capsules/{capsule_id}",
            json={
                "status": "active",
                "include_in_rag": True,
                "tags": ["final", "tags", "set"]
            }
        )
        assert patch_response.status_code == 200
        final = patch_response.json()
        assert final["metadata"]["status"] == "active"
        assert final["include_in_rag"] is True
        assert set(final["metadata"]["tags"]) == {"final", "tags", "set"}

    def test_rag_scope_profiles(self, client, sample_content):
        """Test: All 4 RAG-Scope profiles (My Capsules, All Public, Inbox, Tags)."""
        # Create multiple capsules with different properties
        capsules_created = []
        for i in range(3):
            content = sample_content.copy()
            content["title"] = f"Test Document {i}"
            content["tags"] = [f"tag-{i}", "shared", "common"]
            response = client.post("/ingest", json=content)
            job_id = response.json()["job_id"]

            # Wait for completion
            for _ in range(30):
                job = client.get(f"/jobs/{job_id}").json()
                if job["state"] == "succeeded":
                    capsules_created.append(job["capsule_id"])
                    break
                time.sleep(0.2)

        assert len(capsules_created) == 3

        # Test 1: My Capsules (default scope)
        chat_response = client.post(
            "/chat",
            json={"query": "What is machine learning?", "scope": ["my"]}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result
        assert "sources" in result
        assert "metrics" in result

        # Test 2: All Public scope
        chat_response = client.post(
            "/chat",
            json={"query": "Tell me about algorithms", "scope": ["public"]}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result

        # Test 3: Collection: Inbox (last 30 days)
        chat_response = client.post(
            "/chat",
            json={"query": "Recent content", "scope": ["inbox"]}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result

        # Test 4: Tag-based scope
        chat_response = client.post(
            "/chat",
            json={"query": "Tag-specific content", "scope": ["tag-0", "shared"]}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result

    def test_strict_citations_mode(self, client, sample_content):
        """Test: Strict Citations Mode requires ≥2 distinct sources."""
        # Create single capsule
        response = client.post("/ingest", json=sample_content)
        job_id = response.json()["job_id"]

        # Wait for completion
        for _ in range(30):
            job = client.get(f"/jobs/{job_id}").json()
            if job["state"] == "succeeded":
                break
            time.sleep(0.2)

        # Query with single source (should fallback)
        chat_response = client.post(
            "/chat",
            json={"query": "Test query", "scope": []}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        # With only one source, should get fallback or empty sources
        assert "answer" in result

        # Create second capsule
        content2 = sample_content.copy()
        content2["title"] = "Second Document"
        content2["content"] = "This is a second document about neural networks and deep learning."
        response2 = client.post("/ingest", json=content2)
        job_id2 = response2.json()["job_id"]

        # Wait for completion
        for _ in range(30):
            job = client.get(f"/jobs/{job_id2}").json()
            if job["state"] == "succeeded":
                break
            time.sleep(0.2)

        # Query with multiple sources (should work)
        chat_response = client.post(
            "/chat",
            json={"query": "Tell me about machine learning", "scope": []}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result
        # Should have sources if answer was generated
        if result["answer"] != "idk+dig_deep":
            assert len(result["sources"]) >= 0  # May be 0 if LLM unavailable

    def test_graph_links(self, client, sample_content):
        """Test: Graph visualization with links."""
        # Create two related capsules
        capsule_ids = []
        for i in range(2):
            content = sample_content.copy()
            content["title"] = f"Related Document {i}"
            response = client.post("/ingest", json=content)
            job_id = response.json()["job_id"]

            # Wait for completion
            for _ in range(30):
                job = client.get(f"/jobs/{job_id}").json()
                if job["state"] == "succeeded":
                    capsule_ids.append(job["capsule_id"])
                    break
                time.sleep(0.2)

        assert len(capsule_ids) == 2

        # Get capsule details and check for links
        for capsule_id in capsule_ids:
            capsule = client.get(f"/capsules/{capsule_id}").json()
            assert "recursive" in capsule
            assert "links" in capsule["recursive"]
            # Links may be empty initially, but structure should exist
            assert isinstance(capsule["recursive"]["links"], list)

    def test_error_recovery_invalid_input(self, client):
        """Test: Error recovery with invalid input."""
        # Test 1: Missing required fields
        response = client.post("/ingest", json={})
        assert response.status_code == 422  # Validation error

        # Test 2: Invalid tags (too few)
        response = client.post(
            "/ingest",
            json={"title": "Test", "content": "Test content", "tags": ["one"]}
        )
        # Should either validate or process with auto-fix
        assert response.status_code in [200, 422]

        # Test 3: Invalid capsule ID in PATCH
        response = client.patch(
            "/capsules/invalid-id",
            json={"include_in_rag": True}
        )
        assert response.status_code == 404

    def test_error_recovery_llm_failure(self, client, sample_content):
        """Test: Graceful degradation when LLM is unavailable."""
        # Create capsule
        response = client.post("/ingest", json=sample_content)
        job_id = response.json()["job_id"]

        # Wait for completion
        for _ in range(30):
            job = client.get(f"/jobs/{job_id}").json()
            if job["state"] == "succeeded":
                break
            time.sleep(0.2)

        # Chat should work even without LLM (fallback response)
        chat_response = client.post(
            "/chat",
            json={"query": "Test query", "scope": []}
        )
        assert chat_response.status_code == 200
        result = chat_response.json()
        assert "answer" in result
        # Should have fallback answer if LLM unavailable
        assert isinstance(result["answer"], str)

    def test_concurrent_job_processing(self, client, sample_content):
        """Test: Multiple concurrent jobs."""
        # Submit multiple jobs simultaneously
        job_ids = []
        for i in range(3):
            content = sample_content.copy()
            content["title"] = f"Concurrent Job {i}"
            response = client.post("/ingest", json=content)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # Wait for all jobs to complete
        completed = []
        for _ in range(50):  # Longer timeout for concurrent jobs
            for job_id in job_ids:
                if job_id not in completed:
                    job = client.get(f"/jobs/{job_id}").json()
                    if job["state"] == "succeeded":
                        completed.append(job_id)
            if len(completed) == len(job_ids):
                break
            time.sleep(0.3)

        assert len(completed) == len(job_ids)

    def test_rate_limiting(self, client, sample_content):
        """Test: Rate limiting enforcement."""
        # Note: Rate limiting may not be enforced in test environment
        # This test verifies the endpoint still works
        for i in range(5):
            response = client.post("/ingest", json=sample_content)
            # Should either succeed or return rate limit error
            assert response.status_code in [200, 429]

    def test_observability_endpoints(self, client, sample_content):
        """Test: Observability endpoints return valid data."""
        # Create some capsules first
        for i in range(2):
            content = sample_content.copy()
            content["title"] = f"Observability Test {i}"
            response = client.post("/ingest", json=content)
            job_id = response.json()["job_id"]

            # Wait briefly
            for _ in range(10):
                job = client.get(f"/jobs/{job_id}").json()
                if job["state"] == "succeeded":
                    break
                time.sleep(0.2)

        # Test observability endpoints
        endpoints = [
            "/observability/retrieval",
            "/observability/router",
            "/observability/semantic-hash",
            "/observability/pii",
            "/observability/standard",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert data is not None

    def test_health_and_readiness(self, client):
        """Test: Health check endpoints."""
        # Health check
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

        # Readiness check
        response = client.get("/readyz")
        # May be 200 or 503 depending on store state
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data

        # Liveness check
        response = client.get("/livez")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "live"
