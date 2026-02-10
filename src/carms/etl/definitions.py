"""Dagster definitions - assets, resources, jobs."""

import os

from dagster import Definitions, define_asset_job, load_assets_from_package_module

from carms.etl import assets
from carms.etl.resources import DatabaseResource, EmbeddingResource

database_url = os.environ.get("DATABASE_URL", "postgresql://carms:carms@localhost:5432/carms")
embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
openai_api_key = os.environ.get("OPENAI_API_KEY", "")

all_assets = load_assets_from_package_module(assets)

full_refresh_job = define_asset_job(
    name="full_refresh",
    selection="*",
    description="Materialize all assets: raw data → staging → embeddings",
)

defs = Definitions(
    assets=all_assets,
    jobs=[full_refresh_job],
    resources={
        "database": DatabaseResource(database_url=database_url),
        "embeddings": EmbeddingResource(model_name=embedding_model, openai_api_key=openai_api_key),
    },
)
