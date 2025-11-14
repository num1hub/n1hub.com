"""Tests for CapsuleValidator."""

import pytest
from datetime import datetime, timezone

from app.models import (
    CapsuleModel,
    CapsuleMetadata,
    CapsuleCorePayload,
    CapsuleNeuroConcentrate,
    CapsuleRecursive,
    SourceDescriptor,
)
from app.validators import CapsuleValidator


def create_test_capsule(**overrides) -> CapsuleModel:
    """Create a test capsule with defaults."""
    defaults = {
        "capsule_id": "01JGXM0000000000000000TEST",
        "version": "1.0.0",
        "status": "active",
        "author": "test",
        "created_at": datetime.now(timezone.utc),
        "language": "en",
        "source": SourceDescriptor(type="text", uri=None),
        "tags": ["test", "capsule", "validation"],
        "length": {"chars": 1000, "tokens_est": 250},
        "semantic_hash": "test-capsule-validation-summary-keywords-vector-hint-archetypes",
    }
    defaults.update(overrides.get("metadata", {}))
    
    metadata = CapsuleMetadata(**defaults)
    
    core_defaults = {
        "content_type": "text/markdown",
        "content": "Test content for validation",
        "truncation_note": None,
    }
    core_defaults.update(overrides.get("core_payload", {}))
    core_payload = CapsuleCorePayload(**core_defaults)
    
    neuro_defaults = {
        "summary": " ".join(["word"] * 100),  # 100 words
        "keywords": ["test", "capsule", "validation", "summary", "keywords"],
        "entities": [],
        "claims": [],
        "insights": [],
        "questions": [],
        "archetypes": ["operator"],
        "symbols": [],
        "emotional_charge": 0.0,
        "vector_hint": ["test", "capsule", "validation", "summary", "keywords", "vector", "hint", "anchor"],
        "semantic_hash": "test-capsule-validation-summary-keywords-vector-hint-archetypes",
    }
    neuro_defaults.update(overrides.get("neuro_concentrate", {}))
    neuro_concentrate = CapsuleNeuroConcentrate(**neuro_defaults)
    
    recursive_defaults = {
        "links": [],
        "actions": [],
        "prompts": [],
        "confidence": 0.9,
    }
    recursive_defaults.update(overrides.get("recursive", {}))
    recursive = CapsuleRecursive(**recursive_defaults)
    
    return CapsuleModel(
        include_in_rag=True,
        metadata=metadata,
        core_payload=core_payload,
        neuro_concentrate=neuro_concentrate,
        recursive=recursive,
    )


@pytest.mark.asyncio
async def test_validator_passes_valid_capsule():
    """Test validator passes a valid capsule."""
    capsule = create_test_capsule()
    validator = CapsuleValidator(strict_mode=False)
    is_valid, errors, warnings = await validator.validate(capsule)
    assert is_valid is True
    assert len(errors) == 0


@pytest.mark.asyncio
async def test_validator_fixes_summary_length():
    """Test validator auto-fixes summary length violations."""
    # Too short
    capsule = create_test_capsule(
        neuro_concentrate={"summary": " ".join(["word"] * 50)}  # 50 words
    )
    validator = CapsuleValidator(strict_mode=False)
    is_valid, errors, warnings = await validator.validate(capsule)
    assert len(errors) > 0
    assert any("summary" in e.path.lower() for e in errors)
    assert len(validator.auto_fixes) > 0
    
    # Too long
    capsule = create_test_capsule(
        neuro_concentrate={"summary": " ".join(["word"] * 150)}  # 150 words
    )
    validator = CapsuleValidator(strict_mode=False)
    is_valid, errors, warnings = await validator.validate(capsule)
    assert len(errors) > 0
    # Should auto-fix by trimming
    assert len(capsule.neuro_concentrate.summary.split()) <= 140


@pytest.mark.asyncio
async def test_validator_fixes_semantic_hash_mismatch():
    """Test validator fixes semantic hash mismatch."""
    capsule = create_test_capsule(
        metadata={"semantic_hash": "different-hash-value"},
        neuro_concentrate={"semantic_hash": "test-capsule-validation-summary-keywords-vector-hint-archetypes"}
    )
    validator = CapsuleValidator(strict_mode=False)
    is_valid, errors, warnings = await validator.validate(capsule)
    assert len(errors) > 0
    assert any("semantic_hash" in e.path for e in errors)
    # Should auto-fix by recomputing and mirroring
    assert capsule.metadata.semantic_hash == capsule.neuro_concentrate.semantic_hash


@pytest.mark.asyncio
async def test_validator_clamps_emotional_charge():
    """Test validator clamps emotional_charge to [-1, 1]."""
    capsule = create_test_capsule(
        neuro_concentrate={"emotional_charge": 1.5}  # Out of range
    )
    validator = CapsuleValidator(strict_mode=False)
    await validator.validate(capsule)
    assert -1.0 <= capsule.neuro_concentrate.emotional_charge <= 1.0


@pytest.mark.asyncio
async def test_validator_expands_keywords():
    """Test validator expands keywords if too few."""
    capsule = create_test_capsule(
        neuro_concentrate={"keywords": ["test", "capsule"]}  # Only 2 keywords
    )
    validator = CapsuleValidator(strict_mode=False)
    is_valid, errors, warnings = await validator.validate(capsule)
    assert len(errors) > 0
    # Should auto-fix by expanding
    assert len(capsule.neuro_concentrate.keywords) >= 5


@pytest.mark.asyncio
async def test_validator_validates_link_confidence():
    """Test validator validates link confidence ranges."""
    from app.models import CapsuleLink
    capsule = create_test_capsule(
        recursive={
            "links": [
                CapsuleLink(
                    rel="references",
                    target_capsule_id="01JGXM0000000000000000TARG",
                    reason="test",
                    confidence=1.5,  # Out of range
                )
            ]
        }
    )
    validator = CapsuleValidator(strict_mode=False)
    await validator.validate(capsule)
    assert 0.0 <= capsule.recursive.links[0].confidence <= 1.0
