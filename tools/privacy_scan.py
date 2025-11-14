#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "N1Hub.com_V0.1_Capsule_EN.approved.v1.2.0.json"

sys.path.append(str(ROOT / "apps" / "engine"))

from app.utils.pii import PII_PATTERNS  # noqa: E402


def _scan_values(values: List[str]) -> List[str]:
    hits: List[str] = []
    for value in values:
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                hits.append(f"{label}:{value}")
    return hits


def _load_spec() -> dict:
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"Capsule spec not found at {SPEC_PATH}")
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def main() -> None:
    try:
        spec = _load_spec()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    hits: List[str] = []
    metadata = spec.get("metadata", {})
    neuro = spec.get("neuro_concentrate", {})
    core = spec.get("core_payload", {})

    hits.extend(_scan_values(metadata.get("tags", [])))
    hits.extend(_scan_values(neuro.get("keywords", [])))
    hits.extend(_scan_values(neuro.get("vector_hint", [])))
    hits.extend(_scan_values([neuro.get("summary", ""), core.get("content", "")]))

    if hits:
        print("ERROR: privacy scan detected potential PII:")
        for hit in hits:
            print(f" - {hit}")
        sys.exit(1)

    print("PASS: privacy scan found no PII in sample capsule spec.")


if __name__ == "__main__":
    main()
