"""Seed loader for parsing 20-pack.txt with idempotent seeding."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Import _parse_capsule_from_json from parent bootstrap.py module
# Since bootstrap.py and bootstrap/ coexist, we use importlib
_bootstrap_path = Path(__file__).parent.parent / "bootstrap.py"
spec = importlib.util.spec_from_file_location("app.bootstrap", _bootstrap_path)
bootstrap_module = importlib.util.module_from_spec(spec)
sys.modules["app.bootstrap"] = bootstrap_module
spec.loader.exec_module(bootstrap_module)
_parse_capsule_from_json = bootstrap_module._parse_capsule_from_json

from ..store import BaseCapsuleStore
from ..vectorizer import get_vectorizer


async def load_20_pack_capsules(
    store: BaseCapsuleStore, pack_path: str = "20-pack.txt"
) -> int:
    """Load all 20 CapsuleOS capsules from 20-pack.txt (idempotent)."""
    pack_file = Path(pack_path)
    if not pack_file.exists():
        return 0

    content = pack_file.read_text(encoding="utf-8")
    sections = content.split("---")
    loaded = 0

    # Get existing capsules for idempotency check
    existing_capsules = await store.list_capsules()
    existing_ids = {c.metadata.capsule_id for c in existing_capsules}

    for section in sections:
        section = section.strip()
        if not section or not section.startswith(("{", "1:", "2:", "3:")):
            continue

        try:
            # Extract JSON (handle numbered prefixes like "1:", "2:", etc.)
            lines = section.split("\n")
            json_start = next(
                (i for i, line in enumerate(lines) if line.strip().startswith("{")), None
            )
            if json_start is None:
                continue

            json_text = "\n".join(lines[json_start:])
            data = json.loads(json_text)

            # Parse capsule
            capsule = _parse_capsule_from_json(data)

            # Check if exists (idempotency)
            if capsule.metadata.capsule_id in existing_ids:
                continue  # Skip if exists

            # Save capsule
            await store.save_capsule(capsule)

            # Save embedding
            vectorizer = get_vectorizer()
            text = f"{capsule.neuro_concentrate.summary} {' '.join(capsule.neuro_concentrate.keywords)}"
            embedding = vectorizer.embed(text)
            await store.save_vector(capsule.metadata.capsule_id, embedding)

            loaded += 1
        except Exception as e:
            print(f"Failed to load capsule: {e}")
            continue

    return loaded
