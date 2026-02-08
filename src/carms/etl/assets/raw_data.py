"""Raw data ingestion assets - load source files into DataFrames."""

import json
from pathlib import Path

import pandas as pd
from dagster import AssetExecutionContext, asset


def _data_dir() -> Path:
    """Resolve data directory from env or default."""
    import os

    return Path(os.environ.get("DATA_DIR", "data/raw"))


@asset(group_name="raw", compute_kind="pandas")
def raw_disciplines(context: AssetExecutionContext) -> pd.DataFrame:
    """Load discipline reference data from Excel."""
    path = _data_dir() / "1503_discipline.xlsx"
    df = pd.read_excel(path)
    context.log.info(f"Loaded {len(df)} disciplines from {path}")
    return df


@asset(group_name="raw", compute_kind="pandas")
def raw_program_master(context: AssetExecutionContext) -> pd.DataFrame:
    """Load program master data from Excel."""
    path = _data_dir() / "1503_program_master.xlsx"
    df = pd.read_excel(path)
    # Drop the unnamed index column if present
    if df.columns[0] is None or str(df.columns[0]).startswith("Unnamed"):
        df = df.drop(df.columns[0], axis=1)
    context.log.info(f"Loaded {len(df)} programs from {path}")
    return df


@asset(group_name="raw", compute_kind="pandas")
def raw_descriptions_sectioned(context: AssetExecutionContext) -> pd.DataFrame:
    """Load sectioned program descriptions from CSV."""
    path = _data_dir() / "1503_program_descriptions_x_section.csv"
    df = pd.read_csv(path)
    # Drop the unnamed index column if present
    if df.columns[0] is None or str(df.columns[0]).startswith("Unnamed"):
        df = df.drop(df.columns[0], axis=1)
    context.log.info(f"Loaded {len(df)} descriptions from {path}")
    return df


@asset(group_name="raw", compute_kind="python")
def raw_markdown_documents(context: AssetExecutionContext) -> list[dict]:
    """Load full markdown program descriptions from JSON."""
    path = _data_dir() / "1503_markdown_program_descriptions_v2.json"
    with open(path) as f:
        docs = json.load(f)
    context.log.info(f"Loaded {len(docs)} markdown documents from {path}")
    return docs
