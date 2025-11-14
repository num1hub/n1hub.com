"""Tests for error taxonomy and recovery system."""

import pytest

from app.errors.taxonomy import (
    ErrorCategory,
    ErrorCode,
    CapsuleError,
    ErrorRecovery,
    categorize_error,
    build_error,
)


def test_error_category_enum():
    """Test ErrorCategory enum values."""
    assert ErrorCategory.VALIDATION_SCHEMA == "validation.schema"
    assert ErrorCategory.DATA_MISSING == "data.missing"
    assert ErrorCategory.PRIVACY_CONFLICT == "privacy.conflict"


def test_error_code_enum():
    """Test ErrorCode enum values."""
    assert ErrorCode.SUMMARY_LENGTH_VIOLATION == "summary_length_violation"
    assert ErrorCode.SEMANTIC_HASH_MISMATCH == "semantic_hash_mismatch"
    assert ErrorCode.PII_IN_METADATA == "pii_in_metadata"


def test_categorize_error():
    """Test error code to category mapping."""
    assert categorize_error("summary_length_violation") == ErrorCategory.VALIDATION_SCHEMA
    assert categorize_error("pii_detected_in_content") == ErrorCategory.PRIVACY_CONFLICT
    assert categorize_error("semantic_duplicate_candidate") == ErrorCategory.DUPLICATION_INTEGRITY
    assert categorize_error("unknown_code") == ErrorCategory.VALIDATION_SCHEMA  # default


def test_build_error():
    """Test building structured errors."""
    error = build_error(
        ErrorCode.SUMMARY_LENGTH_VIOLATION,
        field="/neuro_concentrate/summary",
        message="Summary has 152 words; exceeds maximum 140",
        remedy="Trim to 140 words or expand to 70 words from source",
        severity="error",
        auto_fixable=True,
    )
    assert error.category == ErrorCategory.VALIDATION_SCHEMA
    assert error.code == ErrorCode.SUMMARY_LENGTH_VIOLATION
    assert error.field == "/neuro_concentrate/summary"
    assert error.auto_fixable is True


def test_error_recovery_can_auto_fix():
    """Test auto-fix detection."""
    auto_fixable = build_error(
        ErrorCode.SUMMARY_LENGTH_VIOLATION,
        field="/neuro_concentrate/summary",
        message="test",
        remedy="test",
        auto_fixable=True,
    )
    assert ErrorRecovery.can_auto_fix(auto_fixable) is True

    manual_fix = build_error(
        ErrorCode.MISSING_REQUIRED_FIELD,
        field="/metadata/author",
        message="test",
        remedy="test",
        auto_fixable=False,
    )
    assert ErrorRecovery.can_auto_fix(manual_fix) is False


def test_error_recovery_strategy():
    """Test recovery strategy retrieval."""
    error = build_error(
        ErrorCode.SUMMARY_LENGTH_VIOLATION,
        field="/neuro_concentrate/summary",
        message="test",
        remedy="test",
    )
    strategy = ErrorRecovery.get_recovery_strategy(error)
    assert "Trim to 140 words" in strategy or "expand to 70 words" in strategy
