"""Base report class and metadata for the reporting framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlmodel import Session


@dataclass
class ReportMetadata:
    """Metadata describing a generated report."""

    name: str
    title: str
    description: str
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    row_count: int = 0
    columns: list[str] = field(default_factory=list)


class BaseReport(ABC):
    """Abstract base class for all CaRMS reports.

    Subclasses implement ``generate()`` to produce a DataFrame using pandas.
    ``to_json()`` and ``to_csv()`` are provided for free.
    """

    name: str
    title: str
    description: str

    @abstractmethod
    def generate(self, session: Session) -> pd.DataFrame:
        """Run the report query and return a DataFrame."""

    def to_json(self, session: Session) -> dict:
        """Generate the report and return as JSON-serializable dict."""
        df = self.generate(session)
        metadata = ReportMetadata(
            name=self.name,
            title=self.title,
            description=self.description,
            row_count=len(df),
            columns=list(df.columns),
        )
        return {
            "metadata": {
                "name": metadata.name,
                "title": metadata.title,
                "description": metadata.description,
                "generated_at": metadata.generated_at,
                "row_count": metadata.row_count,
                "columns": metadata.columns,
            },
            "data": df.to_dict(orient="records"),
        }

    def to_csv(self, session: Session, path: Path) -> Path:
        """Generate the report and write to CSV."""
        df = self.generate(session)
        path = Path(path)
        df.to_csv(path, index=False)
        return path
