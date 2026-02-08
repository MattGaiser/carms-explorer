"""Dagster resources for database and embedding operations."""

from dagster import ConfigurableResource
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine
from sqlmodel import Session


class DatabaseResource(ConfigurableResource):
    """Database connection resource."""

    database_url: str = "postgresql://carms:carms@localhost:5432/carms"

    def get_engine(self):
        return create_engine(self.database_url, echo=False, pool_pre_ping=True)

    def get_session(self):
        return Session(self.get_engine())


class EmbeddingResource(ConfigurableResource):
    """Sentence embedding resource using all-MiniLM-L6-v2."""

    model_name: str = "all-MiniLM-L6-v2"

    _model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            object.__setattr__(self, "_model", SentenceTransformer(self.model_name))
        return self._model  # type: ignore[return-value]

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
        return embeddings.tolist()
