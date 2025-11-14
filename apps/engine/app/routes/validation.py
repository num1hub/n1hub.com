"""Validation routes for capsule validation."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status

from ..models import CapsuleModel, JobErrorIssue
from ..validators import CapsuleValidator

validation_router = APIRouter(prefix="/validate", tags=["validation"])


@validation_router.post("/capsule")
async def validate_capsule(
    capsule: CapsuleModel,
    strict_mode: bool = False,
) -> dict:
    """Validate a single capsule against schema and guardrails."""
    validator = CapsuleValidator(strict_mode=strict_mode)
    is_valid, errors, warnings = await validator.validate(capsule)

    return {
        "ok": is_valid,
        "errors": [{"path": e.path, "message": e.message} for e in errors],
        "warnings": [{"path": w.path, "message": w.message} for w in warnings],
        "auto_fixes_applied": validator.auto_fixes,
        "capsule": capsule.model_dump() if is_valid else None,
    }


@validation_router.post("/batch")
async def validate_batch(
    capsules: List[CapsuleModel],
    strict_mode: bool = False,
) -> dict:
    """Validate multiple capsules in batch."""
    results = []
    total_errors = 0
    total_warnings = 0

    for capsule in capsules:
        validator = CapsuleValidator(strict_mode=strict_mode)
        is_valid, errors, warnings = await validator.validate(capsule)
        results.append(
            {
                "capsule_id": capsule.metadata.capsule_id,
                "ok": is_valid,
                "errors": [{"path": e.path, "message": e.message} for e in errors],
                "warnings": [{"path": w.path, "message": w.message} for w in warnings],
                "auto_fixes_applied": validator.auto_fixes.copy(),
            }
        )
        total_errors += len(errors)
        total_warnings += len(warnings)

    return {
        "ok": total_errors == 0,
        "total": len(capsules),
        "valid": sum(1 for r in results if r["ok"]),
        "invalid": sum(1 for r in results if not r["ok"]),
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "results": results,
    }
