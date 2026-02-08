"""Embedding model management for search queries."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from carms.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    return SentenceTransformer(settings.embedding_model)


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    model = get_embedding_model()
    vector = model.encode(query, normalize_embeddings=True)
    return vector.tolist()
