from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for typing
    from ..models import CapsuleModel

_PATTERN_DEFINITIONS: Dict[str, str] = {
    "email": r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    "phone": r"\+?\d[\d \-]{7,}\d",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "tax_id": r"\b\d{2}-\d{7}\b",
    "id_number": r"\b[A-Z]{1,3}\d{6,10}\b",
}
PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    label: re.compile(pattern, re.IGNORECASE) for label, pattern in _PATTERN_DEFINITIONS.items()
}


def redact_pii(text: str) -> str:
    """Replace matched PII tokens with deterministic placeholders."""
    for label, pattern in PII_PATTERNS.items():
        text = pattern.sub(lambda match, tag=label: f"[REDACTED:{tag.upper()}]", text)
    return text


def _find_matches(text: str) -> List[Tuple[str, str]]:
    hits: List[Tuple[str, str]] = []
    for label, pattern in PII_PATTERNS.items():
        for match in pattern.findall(text):
            hits.append((label, match if isinstance(match, str) else "".join(match)))
    return hits


def scan_tokens(tokens: Sequence[str]) -> List[str]:
    hits: List[str] = []
    for token in tokens:
        hits.extend(f"{label}:{token}" for label, _match in _find_matches(token))
    return hits


def scan_capsule_for_pii(capsule: "CapsuleModel") -> List[str]:
    """Scan the capsule summary/tags/keywords/vector hints for PII."""
    hits: List[str] = []
    hits.extend(entry for entry in scan_tokens(capsule.metadata.tags))
    hits.extend(entry for entry in scan_tokens(capsule.neuro_concentrate.keywords))
    hits.extend(entry for entry in scan_tokens(capsule.neuro_concentrate.vector_hint))
    hits.extend(f"summary:{label}" for label, _ in _find_matches(capsule.neuro_concentrate.summary))
    hits.extend(f"core:{label}" for label, _ in _find_matches(capsule.core_payload.content))
    return hits


def scan_materials(inputs: Iterable[str]) -> List[str]:
    hits: List[str] = []
    for item in inputs:
        hits.extend(f"{label}:{match}" for label, match in _find_matches(item))
    return hits


def contains_pii_in_metadata_field(field_values: Sequence[str]) -> bool:
    """Check if metadata field (tags, keywords, vector_hint) contains PII.
    
    Args:
        field_values: List of strings to check (e.g., tags, keywords, vector_hint)
    
    Returns:
        True if any PII pattern matches, False otherwise
    """
    for value in field_values:
        if _find_matches(value):
            return True
    return False
