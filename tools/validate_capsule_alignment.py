#!/usr/bin/env python3

"""
Lightweight validator that ensures the working tree still aligns with the
N1Hub.com v0.1 capsule specification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "N1Hub.com_V0.1_Capsule_EN.approved.v1.2.0.json"
REQUIRED_SECTIONS = ["metadata", "core_payload", "neuro_concentrate", "recursive"]
REQUIRED_PATHS = [
    "app/page.tsx",
    "app/chat/page.tsx",
    "app/capsules/page.tsx",
    "app/capsules/[id]/page.tsx",
    "app/api/capsules/route.ts",
    "app/api/jobs/route.ts",
    "app/api/events/stream/route.ts",
    "apps/engine/app/pipeline.py",
    "apps/engine/app/observability.py",
    "apps/engine/app/utils/pii.py",
    "infra/sql/0001_capsule_store.sql",
    "config/.env.example",
]


def _validate_spec() -> List[str]:
    if not SPEC_PATH.exists():
        return ["Capsule spec file is missing."]

    errors: List[str] = []
    data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    for section in REQUIRED_SECTIONS:
        if section not in data:
            errors.append(f"Spec missing section: {section}")

    if "metadata" in data and "neuro_concentrate" in data:
        meta_hash = data["metadata"].get("semantic_hash")
        neuro_hash = data["neuro_concentrate"].get("semantic_hash")
        if meta_hash != neuro_hash:
            errors.append("semantic_hash mismatch between metadata and neuro_concentrate.")

    core = data.get("core_payload", {})
    if not core.get("content"):
        errors.append("core_payload.content is empty.")

    return errors


def _validate_paths() -> List[str]:
    errors: List[str] = []
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).exists():
            errors.append(f"Missing required path: {relative}")
    return errors


def main() -> None:
    issues = _validate_spec()
    issues.extend(_validate_paths())

    if issues:
        print("FAIL: repo is not aligned with the capsule spec.")
        for issue in issues:
            print(f"- {issue}")
        sys.exit(1)

    print("PASS: capsule spec + repo alignment checks succeeded.")


if __name__ == "__main__":
    main()
