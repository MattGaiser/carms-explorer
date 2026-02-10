"""Dagster resources for database and embedding operations."""

from dagster import ConfigurableResource
from langchain_openai import OpenAIEmbeddings
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
    """OpenAI embedding resource using text-embedding-3-small."""

    model_name: str = "text-embedding-3-small"
    openai_api_key: str = ""

    _model: OpenAIEmbeddings | None = None

    def _get_model(self) -> OpenAIEmbeddings:
        if self._model is None:
            object.__setattr__(
                self,
                "_model",
                OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=self.openai_api_key,
                ),
            )
        return self._model  # type: ignore[return-value]

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        return model.embed_documents(texts)
