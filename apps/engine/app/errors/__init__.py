"""Error taxonomy and recovery system for CapsuleOS compliance."""

from .taxonomy import (
    ErrorCategory,
    ErrorCode,
    CapsuleError,
    ErrorRecovery,
    categorize_error,
    build_error,
)

__all__ = [
    "ErrorCategory",
    "ErrorCode",
    "CapsuleError",
    "ErrorRecovery",
    "categorize_error",
    "build_error",
]
