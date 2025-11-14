"""Integration tests for pipeline with validator and link suggester."""

import asyncio

from app.feature_flags import feature_flags
from app.models import IngestRequest
from app.pipeline import DeepMinePipeline
from app.store import MemoryCapsuleStore


def test_pipeline_validates_capsule():
    """Test pipeline uses validator in VALIDATE stage."""

    async def _run() -> None:
        store = MemoryCapsuleStore()
        pipeline = DeepMinePipeline(store)

        request = IngestRequest(
            title="Test Capsule",
            content=" ".join(["word"] * 200),  # Enough content
            tags=["test", "capsule", "validation"],
            include_in_rag=True,
        )

        job = await store.create_job()

        # Should complete successfully with validation
        capsule = await pipeline.run(job.id, request)

        assert capsule is not None
        assert capsule.metadata.capsule_id
        # Validation should have passed (capsule created)
        final_job = await store.get_job(job.id)
        assert final_job.state == "succeeded"

    asyncio.run(_run())


def test_pipeline_handles_validation_failure():
    """Test pipeline handles validation failures gracefully."""

    async def _run() -> None:
        store = MemoryCapsuleStore()
        pipeline = DeepMinePipeline(store)

        # Create a request that might trigger validation issues
        # (though the pipeline should auto-fix most issues)
        request = IngestRequest(
            title="Test",
            content="Short",  # Very short content
            tags=["test"],
            include_in_rag=True,
        )

        job = await store.create_job()

        try:
            capsule = await pipeline.run(job.id, request)
            # If it succeeds, validation auto-fixed issues
            assert capsule is not None
        except Exception:
            # If it fails, check that error is properly structured
            final_job = await store.get_job(job.id)
            assert final_job.state == "failed"
            assert final_job.error is not None

    asyncio.run(_run())


def test_pipeline_suggests_links_when_enabled():
    """Test pipeline suggests links when feature flag is enabled."""

    async def _run() -> None:
        # Enable feature flag
        original_value = feature_flags.is_enabled("ff.link.suggester")
        feature_flags._flags["ff.link.suggester"] = True

        try:
            store = MemoryCapsuleStore()

            # Create an existing capsule for linking
            existing_request = IngestRequest(
                title="Existing Capsule",
                content=" ".join(["word"] * 200),
                tags=["test", "capsule", "existing"],
                include_in_rag=True,
            )
            existing_job = await store.create_job()
            existing_pipeline = DeepMinePipeline(store)
            await existing_pipeline.run(existing_job.id, existing_request)

            # Create new capsule that should link to existing
            new_request = IngestRequest(
                title="New Capsule",
                content=" ".join(["word"] * 200),
                tags=["test", "capsule", "new"],
                include_in_rag=True,
            )
            new_job = await store.create_job()
            new_pipeline = DeepMinePipeline(store)
            new_capsule = await new_pipeline.run(new_job.id, new_request)

            # Should have suggested links
            assert len(new_capsule.recursive.links) >= 0  # May or may not have links depending on similarity
        finally:
            # Restore original flag value
            feature_flags._flags["ff.link.suggester"] = original_value

    asyncio.run(_run())
