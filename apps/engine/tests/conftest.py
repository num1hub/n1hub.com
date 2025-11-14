import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import hashlib
from typing import List

import pytest

from app.config import settings
from app import vectorizer as vectorizer_module
from app import rag as rag_module


class _StubVectorizer:
    """Lightweight deterministic vectorizer for tests."""

    def __init__(self) -> None:
        self.dimension = settings.embedding_dimension

    def embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: List[float] = []
        while len(values) < self.dimension:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) == self.dimension:
                    break
        return values


@pytest.fixture(autouse=True)
def stub_vectorizer(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Provide deterministic embeddings for tests unless opted out."""

    if "vectorizer_no_stub" in request.keywords:
        return

    stub = _StubVectorizer()

    monkeypatch.setattr(vectorizer_module, "get_vectorizer", lambda: stub)
    monkeypatch.setattr(vectorizer_module, "_vectorizer_instance", stub, raising=False)
    monkeypatch.setattr(rag_module, "get_vectorizer", lambda: stub, raising=False)
