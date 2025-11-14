from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from ulid import ULID

from .models import (
    CapsuleCorePayload,
    CapsuleLink,
    CapsuleMetadata,
    CapsuleModel,
    CapsuleNeuroConcentrate,
    CapsuleRecursive,
    SourceDescriptor,
)
from .store import BaseCapsuleStore
from .vectorizer import get_vectorizer


async def seed_from_pack(store: BaseCapsuleStore, pack_path: str) -> None:
    """Seed capsules from the 20-pack JSON file (idempotent)."""
    path = Path(pack_path)
    if not path.exists():
        raise FileNotFoundError(f"20-pack file not found: {pack_path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    # Check if index capsule already exists (idempotency check)
    existing_capsules = await store.list_capsules()
    existing_ids = {c.metadata.capsule_id for c in existing_capsules}

    # Create index capsule
    vectorizer = get_vectorizer()
    index_capsule = _parse_capsule_from_json(data)
    if index_capsule.metadata.capsule_id not in existing_ids:
        await store.save_capsule(index_capsule)
        # Generate and save vector
        text = f"{index_capsule.neuro_concentrate.summary} {' '.join(index_capsule.neuro_concentrate.keywords)}"
        embedding = vectorizer.embed(text)
        await store.save_vector(index_capsule.metadata.capsule_id, embedding)

    # Create placeholder capsules for referenced capsule_ids
    referenced_ids = [link["target_capsule_id"] for link in data.get("recursive", {}).get("links", [])]
    for ref_id in referenced_ids:
        if ref_id in existing_ids:
            continue

        # Create minimal placeholder capsule based on index metadata
        placeholder = _create_placeholder_capsule(ref_id, data)
        await store.save_capsule(placeholder)
        text = f"{placeholder.neuro_concentrate.summary} {' '.join(placeholder.neuro_concentrate.keywords)}"
        embedding = vectorizer.embed(text)
        await store.save_vector(placeholder.metadata.capsule_id, embedding)


def _parse_capsule_from_json(data: dict) -> CapsuleModel:
    """Parse a capsule from JSON data."""
    metadata_data = data["metadata"]
    if metadata_data.get("capsule_id") == "PENDING":
        # Generate ULID for pending capsules
        metadata_data["capsule_id"] = str(ULID())

    metadata = CapsuleMetadata(
        capsule_id=metadata_data["capsule_id"],
        version=metadata_data.get("version", "1.0.0"),
        status=metadata_data.get("status", "active"),
        author=metadata_data.get("author", "system"),
        created_at=datetime.fromisoformat(metadata_data["created_at"].replace("Z", "+00:00")),
        language=metadata_data.get("language", "en"),
        source=SourceDescriptor(**metadata_data.get("source", {"type": "derived", "uri": None})),
        tags=metadata_data.get("tags", []),
        length=metadata_data.get("length", {"chars": 0, "tokens_est": 0}),
        semantic_hash=metadata_data["semantic_hash"],
    )

    core_payload = CapsuleCorePayload(
        content_type=data["core_payload"]["content_type"],
        content=data["core_payload"]["content"].replace("\\n", "\n"),
        truncation_note=data["core_payload"].get("truncation_note"),
    )

    neuro_data = data["neuro_concentrate"]
    neuro = CapsuleNeuroConcentrate(
        summary=neuro_data["summary"],
        keywords=neuro_data["keywords"],
        entities=neuro_data.get("entities", []),
        claims=neuro_data.get("claims", []),
        insights=neuro_data.get("insights", []),
        questions=neuro_data.get("questions", []),
        archetypes=neuro_data.get("archetypes", []),
        symbols=neuro_data.get("symbols", []),
        emotional_charge=neuro_data.get("emotional_charge", 0.0),
        vector_hint=neuro_data.get("vector_hint", []),
        semantic_hash=neuro_data["semantic_hash"],
    )

    recursive_data = data.get("recursive", {})
    links = [
        CapsuleLink(
            rel=link["rel"],
            target_capsule_id=link["target_capsule_id"],
            reason=link.get("reason", ""),
            confidence=link.get("confidence", 0.9),
        )
        for link in recursive_data.get("links", [])
    ]

    recursive = CapsuleRecursive(
        links=links,
        actions=recursive_data.get("actions", []),
        prompts=recursive_data.get("prompts", []),
        confidence=recursive_data.get("confidence", 0.9),
    )

    return CapsuleModel(
        include_in_rag=True,
        metadata=metadata,
        core_payload=core_payload,
        neuro_concentrate=neuro,
        recursive=recursive,
    )


def _create_placeholder_capsule(capsule_id: str, index_data: dict) -> CapsuleModel:
    """Create a minimal placeholder capsule for a referenced capsule_id."""
    # Find the link info from index
    link_info = None
    for link in index_data.get("recursive", {}).get("links", []):
        if link["target_capsule_id"] == capsule_id:
            link_info = link
            break

    # Extract title from reason if available
    title = link_info.get("reason", "Capsule").replace("Index entry for ", "") if link_info else "Capsule"

    now = datetime.now(timezone.utc)
    metadata = CapsuleMetadata(
        capsule_id=capsule_id,
        version="1.0.0",
        status="active",
        author="CapsuleOS Core Team",
        created_at=now,
        language="en",
        source=SourceDescriptor(type="derived", uri=None),
        tags=["capsuleos", "placeholder", "seed"],
        length={"chars": 100, "tokens_est": 25},
        semantic_hash=f"placeholder-{capsule_id[:8]}",
    )

    core_payload = CapsuleCorePayload(
        content_type="text/markdown",
        content=f"# {title}\n\nPlaceholder capsule for {capsule_id}. This capsule is part of the CapsuleOS 20-pack seed collection.",
        truncation_note=None,
    )

    neuro = CapsuleNeuroConcentrate(
        summary=f"Placeholder capsule {title} from CapsuleOS 20-pack seed collection.",
        keywords=["capsuleos", "seed", "placeholder", title.lower().split()[0] if title else "capsule"],
        entities=[{"type": "concept", "name": title}],
        claims=[f"This is a placeholder for {title}."],
        insights=["Part of the CapsuleOS 20-pack seed collection."],
        questions=["What is the full content of this capsule?"],
        archetypes=["operator", "knowledge-engineer"],
        symbols=["capsule", "seed"],
        emotional_charge=0.0,
        vector_hint=["capsuleos", "seed", title.lower().split()[0] if title else "capsule"],
        semantic_hash=f"placeholder-{capsule_id[:8]}",
    )

    recursive = CapsuleRecursive(
        links=[],
        actions=[],
        prompts=[],
        confidence=0.5,
    )

    return CapsuleModel(
        include_in_rag=True,
        metadata=metadata,
        core_payload=core_payload,
        neuro_concentrate=neuro,
        recursive=recursive,
    )
