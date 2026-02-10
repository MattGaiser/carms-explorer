"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "postgresql://carms:carms@localhost:5432/carms"
    dagster_database_url: str = "postgresql://carms:carms@localhost:5432/dagster"

    # Embeddings (OpenAI)
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    openai_api_key: str | None = None
    chunk_size: int = 512
    chunk_overlap: int = 64

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Agent (optional)
    anthropic_api_key: str | None = None

    # Data
    data_dir: str = "data/raw"


settings = Settings()
