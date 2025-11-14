from app.config import settings
from app.pipeline import DeepMinePipeline
from app.store import MemoryCapsuleStore
from app import vectorizer as vectorizer_module


class DummyEmbedding:
    def __init__(self, dim: int) -> None:
        self._data = [0.0] * dim

    def tolist(self) -> list[float]:
        return self._data


class DummySentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, text: str, convert_to_numpy: bool = True, normalize_embeddings: bool = True):
        return DummyEmbedding(settings.embedding_dimension)

    def get_sentence_embedding_dimension(self) -> int:
        return settings.embedding_dimension


def _fresh_vectorizer(monkeypatch) -> vectorizer_module.Vectorizer:
    vectorizer_module.Vectorizer._model = None
    vectorizer_module._vectorizer_instance = None
    monkeypatch.setattr(vectorizer_module, "SentenceTransformer", DummySentenceTransformer)
    return vectorizer_module.get_vectorizer()


def test_vectorizer_honors_configured_dimension(monkeypatch):
    vectorizer = _fresh_vectorizer(monkeypatch)
    embedding = vectorizer.embed("test capsule")
    assert len(embedding) == settings.embedding_dimension
    assert vectorizer.dimension == settings.embedding_dimension


def test_chunk_ids_are_deterministic():
    pipeline = DeepMinePipeline(MemoryCapsuleStore())
    payload = "signal " * (settings.rag_chunk_size * 2)
    segments = pipeline._segment(payload.strip())
    metadata = pipeline._assign_chunk_ids("01FZ9Z00000000000000000000", segments)
    assert len(metadata) > 1
    assert metadata[0]["chunk_id"].startswith("01FZ9Z00000000000000000000::c0001@t0-")
    assert metadata[1]["chunk_id"].startswith("01FZ9Z00000000000000000000::c0002@t")
    assert metadata[0]["chunk_id"].endswith(f"-{metadata[0]['end_token']}")
