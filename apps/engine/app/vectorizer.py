from __future__ import annotations

import threading
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from .config import settings


class Vectorizer:
    """
    Singleton-style vectorizer that loads a sentence-transformers model
    and provides embedding functionality for semantic search.
    
    Thread-safe initialization ensures the model is loaded only once.
    """
    
    _instance: Optional[Vectorizer] = None
    _lock = threading.Lock()
    _model: Optional[SentenceTransformer] = None
    
    def __init__(self) -> None:
        """Initialize the vectorizer and load the model."""
        if Vectorizer._model is None:
            with Vectorizer._lock:
                if Vectorizer._model is None:
                    model_name = settings.embedding_model
                    Vectorizer._model = SentenceTransformer(model_name)
                    actual_dim = Vectorizer._model.get_sentence_embedding_dimension()
                    if actual_dim != settings.embedding_dimension:
                        raise RuntimeError(
                            f"Embedding dimension mismatch: model={actual_dim} config={settings.embedding_dimension}"
                        )
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if Vectorizer._model is None:
            raise RuntimeError("Vectorizer model not initialized")
        
        # sentence-transformers encode returns numpy array, convert to list
        embedding = Vectorizer._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        data = embedding.tolist()
        if len(data) != settings.embedding_dimension:
            raise RuntimeError(
                f"Vectorizer returned {len(data)} dims but config expects {settings.embedding_dimension}"
            )
        return data
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return settings.embedding_dimension


# Global singleton instance
_vectorizer_instance: Optional[Vectorizer] = None


def get_vectorizer() -> Vectorizer:
    """
    Get or create the global Vectorizer instance.
    
    This function can be used as a FastAPI dependency:
    \`\`\`python
    @app.get("/endpoint")
    async def endpoint(vectorizer: Vectorizer = Depends(get_vectorizer)):
        ...
    \`\`\`
    """
    global _vectorizer_instance
    if _vectorizer_instance is None:
        _vectorizer_instance = Vectorizer()
    return _vectorizer_instance
