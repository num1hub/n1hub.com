"""Error Taxonomy & Recovery - based on CapsuleOS 20-pack #14."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel


class ErrorCategory(str, Enum):
    """Error category classification."""

    VALIDATION_SCHEMA = "validation.schema"
    DATA_MISSING = "data.missing"
    PRIVACY_CONFLICT = "privacy.conflict"
    DUPLICATION_INTEGRITY = "duplication.integrity"
    SIZE_LIMITS = "size.limits"
    LINK_INTEGRITY = "link.integrity"


class ErrorCode(str, Enum):
    """Specific error codes within categories."""

    # validation.schema
    MISSING_REQUIRED_FIELD = "missing_required_field"
    WRONG_TYPE = "wrong_type"
    ENUM_OUT_OF_RANGE = "enum_out_of_range"
    BAD_ULID_LENGTH = "bad_ulid_length"
    BAD_BCP47 = "bad_bcp47"
    ISO8601_TIMESTAMP_INVALID = "iso8601_timestamp_invalid"
    SUMMARY_LENGTH_VIOLATION = "summary_length_violation"
    KEYWORD_COUNT_VIOLATION = "keyword_count_violation"
    VECTOR_HINT_COUNT_VIOLATION = "vector_hint_count_violation"
    ARCHETYPES_COUNT_VIOLATION = "archetypes_count_violation"
    EMOTIONAL_CHARGE_OUT_OF_RANGE = "emotional_charge_out_of_range"
    SEMANTIC_HASH_MISMATCH = "semantic_hash_mismatch"
    LINK_REL_INVALID = "link_rel_invalid"
    LINK_CONFIDENCE_OUT_OF_RANGE = "link_confidence_out_of_range"
    SECTION_MISSING = "section_missing"
    EXTRA_SECTIONS = "extra_sections"

    # data.missing
    INSUFFICIENT_MATERIAL = "insufficient_material"
    AMBIGUOUS_LANGUAGE = "ambiguous_language"
    MISSING_CREATED_AT = "missing_created_at"
    MISSING_AUTHOR = "missing_author"
    MISSING_TAGS = "missing_tags"
    MISSING_SOURCE_TYPE = "missing_source_type"

    # privacy.conflict
    PII_DETECTED_IN_CONTENT = "pii_detected_in_content"
    PII_IN_METADATA = "pii_in_metadata"
    SECRET_LEAK = "secret_leak"
    OVER_REDACTION = "over_redaction"

    # duplication.integrity
    SEMANTIC_DUPLICATE_CANDIDATE = "semantic_duplicate_candidate"
    DUPLICATE_CAPSULE_EDGE_NEEDED = "duplicate_capsule_edge_needed"
    NEAR_DUPLICATE_UNLINKED = "near_duplicate_unlinked"

    # size.limits
    CONTENT_EXCEEDS_BUDGET = "content_exceeds_budget"
    NEEDS_TRUNCATION_WITH_NOTE = "needs_truncation_with_note"

    # link.integrity
    INVALID_TARGET_ID = "invalid_target_id"
    UNKNOWN_RELATION = "unknown_relation"
    SELF_LINK = "self_link"
    DUPLICATE_EDGE = "duplicate_edge"
    MISSING_REASON = "missing_reason"


class CapsuleError(BaseModel):
    """Structured error with recovery guidance."""

    category: ErrorCategory
    code: ErrorCode
    field: str
    message: str
    remedy: str
    severity: Literal["error", "warning", "critical"]
    auto_fixable: bool = False


class ErrorRecovery:
    """Recovery strategies for different error categories."""

    @staticmethod
    def can_auto_fix(error: CapsuleError) -> bool:
        """Check if error can be auto-fixed deterministically."""
        auto_fixable_codes = {
            ErrorCode.SUMMARY_LENGTH_VIOLATION,
            ErrorCode.KEYWORD_COUNT_VIOLATION,
            ErrorCode.VECTOR_HINT_COUNT_VIOLATION,
            ErrorCode.ARCHETYPES_COUNT_VIOLATION,
            ErrorCode.EMOTIONAL_CHARGE_OUT_OF_RANGE,
            ErrorCode.SEMANTIC_HASH_MISMATCH,
            ErrorCode.LINK_CONFIDENCE_OUT_OF_RANGE,
            ErrorCode.ISO8601_TIMESTAMP_INVALID,
        }
        return error.code in auto_fixable_codes

    @staticmethod
    def get_recovery_strategy(error: CapsuleError) -> str:
        """Get recovery strategy description."""
        strategies = {
            ErrorCode.SUMMARY_LENGTH_VIOLATION: "Trim to 140 words or expand to 70 words from source",
            ErrorCode.SEMANTIC_HASH_MISMATCH: "Recompute from summary and mirror to both locations",
            ErrorCode.PII_IN_METADATA: "Remove PII from tags/summary/keywords, set status to draft",
            ErrorCode.SEMANTIC_DUPLICATE_CANDIDATE: "Create duplicates link to canonical capsule",
        }
        return strategies.get(error.code, "Manual review required")


def categorize_error(error_code: str) -> ErrorCategory:
    """Map error code to category."""
    mapping = {
        "missing_required_field": ErrorCategory.VALIDATION_SCHEMA,
        "summary_length_violation": ErrorCategory.VALIDATION_SCHEMA,
        "semantic_hash_mismatch": ErrorCategory.VALIDATION_SCHEMA,
        "pii_detected_in_content": ErrorCategory.PRIVACY_CONFLICT,
        "semantic_duplicate_candidate": ErrorCategory.DUPLICATION_INTEGRITY,
        "content_exceeds_budget": ErrorCategory.SIZE_LIMITS,
        "invalid_target_id": ErrorCategory.LINK_INTEGRITY,
    }
    return mapping.get(error_code, ErrorCategory.VALIDATION_SCHEMA)


def build_error(
    code: ErrorCode,
    field: str,
    message: str,
    remedy: str,
    severity: Literal["error", "warning", "critical"] = "error",
    auto_fixable: bool = False,
) -> CapsuleError:
    """Build a structured error from components."""
    category = categorize_error(code.value)
    return CapsuleError(
        category=category,
        code=code,
        field=field,
        message=message,
        remedy=remedy,
        severity=severity,
        auto_fixable=auto_fixable,
    )
