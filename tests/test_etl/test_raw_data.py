"""Test raw data file parsing."""

import json
from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path("data/raw")


@pytest.mark.skipif(not DATA_DIR.exists(), reason="Data directory not found")
class TestRawFiles:
    def test_discipline_file_loads(self):
        df = pd.read_excel(DATA_DIR / "1503_discipline.xlsx")
        assert len(df) == 37
        assert "discipline_id" in df.columns
        assert "discipline" in df.columns

    def test_program_master_loads(self):
        df = pd.read_excel(DATA_DIR / "1503_program_master.xlsx")
        assert len(df) == 815
        assert "discipline_id" in df.columns
        assert "school_id" in df.columns
        assert "program_stream_id" in df.columns

    def test_descriptions_csv_loads(self):
        df = pd.read_csv(DATA_DIR / "1503_program_descriptions_x_section.csv")
        assert len(df) == 815
        assert "document_id" in df.columns

    def test_markdown_json_loads(self):
        with open(DATA_DIR / "1503_markdown_program_descriptions_v2.json") as f:
            data = json.load(f)
        assert len(data) == 815
        assert "id" in data[0]
        assert "page_content" in data[0]
