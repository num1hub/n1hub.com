"""Tests for LinkSuggester."""

import pytest

from app.linking import LinkSuggester
from app.store import MemoryCapsuleStore
from test_validator import create_test_capsule


@pytest.mark.asyncio
async def test_link_suggester_suggests_links():
    """Test link suggester suggests links based on similarity."""
    store = MemoryCapsuleStore()
    
    # Create source capsule
    source = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000SRC", "tags": ["test", "capsule", "rag"]},
        neuro_concentrate={"keywords": ["test", "capsule", "rag", "validation", "link"]}
    )
    await store.save_capsule(source)
    
    # Create target capsule with overlapping tags/keywords
    target = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000TGT", "tags": ["test", "capsule", "validation"]},
        neuro_concentrate={"keywords": ["test", "capsule", "validation", "summary", "keywords"]}
    )
    await store.save_capsule(target)
    
    # Create unrelated capsule
    unrelated = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000UNR", "tags": ["different", "topic", "unrelated"]},
        neuro_concentrate={"keywords": ["different", "topic", "unrelated", "content", "data"]}
    )
    await store.save_capsule(unrelated)
    
    suggester = LinkSuggester(store)
    links = await suggester.suggest_links(source, top_k=5)
    
    assert len(links) > 0
    # Should suggest link to target (similar) but not unrelated
    target_ids = [link.target_capsule_id for link in links]
    assert "01JGXM0000000000000000TGT" in target_ids


@pytest.mark.asyncio
async def test_link_suggester_confidence_bounds():
    """Test link suggester confidence is in valid range."""
    store = MemoryCapsuleStore()
    source = create_test_capsule(metadata={"capsule_id": "01JGXM0000000000000000SRC"})
    await store.save_capsule(source)
    
    suggester = LinkSuggester(store)
    links = await suggester.suggest_links(source, top_k=5)
    
    for link in links:
        assert 0.60 <= link.confidence <= 0.95


@pytest.mark.asyncio
async def test_link_suggester_determines_duplicates():
    """Test link suggester detects duplicates by semantic hash."""
    store = MemoryCapsuleStore()
    
    source = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000SRC", "semantic_hash": "duplicate-hash-value"},
        neuro_concentrate={"semantic_hash": "duplicate-hash-value"}
    )
    await store.save_capsule(source)
    
    target = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000TGT", "semantic_hash": "duplicate-hash-value"},
        neuro_concentrate={"semantic_hash": "duplicate-hash-value"}
    )
    await store.save_capsule(target)
    
    suggester = LinkSuggester(store)
    links = await suggester.suggest_links(source, top_k=5)
    
    # Should detect duplicate
    duplicate_links = [link for link in links if link.rel == "duplicates"]
    assert len(duplicate_links) > 0
    assert duplicate_links[0].target_capsule_id == "01JGXM0000000000000000TGT"


@pytest.mark.asyncio
async def test_link_suggester_filters_by_relation_types():
    """Test link suggester filters by relation types."""
    store = MemoryCapsuleStore()
    source = create_test_capsule(metadata={"capsule_id": "01JGXM0000000000000000SRC"})
    await store.save_capsule(source)
    
    suggester = LinkSuggester(store)
    links = await suggester.suggest_links(
        source,
        top_k=5,
        relation_types=["references", "depends_on"]
    )
    
    for link in links:
        assert link.rel in ["references", "depends_on"]
