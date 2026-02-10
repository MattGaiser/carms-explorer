"""Embedding model management for search queries."""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from carms.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> OpenAIEmbeddings:
    """Load and cache the OpenAI embedding model."""
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    model = get_embedding_model()
    return model.embed_query(query)
