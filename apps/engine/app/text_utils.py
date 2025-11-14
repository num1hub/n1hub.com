from __future__ import annotations

import re
from typing import Iterable, List

STOPWORDS: set[str] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "for",
    "with",
    "in",
    "on",
    "by",
    "from",
    "as",
    "is",
    "are",
    "be",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "at",
    "into",
    "via",
}


def compute_semantic_hash(summary: str, stopwords: Iterable[str] | None = None) -> str:
    """Generate a deterministic semantic hash from summary text."""
    tokens = summary.lower()
    splits = re.split(r"[^a-z0-9]+", tokens)
    seen: List[str] = []
    stopword_set = set(stopwords or STOPWORDS)
    for token in splits:
        if not token or token in stopword_set or len(token) < 3:
            continue
        if token not in seen:
            seen.append(token)
        if len(seen) == 8:
            break
    while len(seen) < 8:
        seen.append(f"z{len(seen) + 1}")
    return "-".join(seen)
