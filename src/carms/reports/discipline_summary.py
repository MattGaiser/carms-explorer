"""Discipline summary report — programs per discipline with stream breakdown."""

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from carms.reports.base import BaseReport


class DisciplineSummaryReport(BaseReport):
    """Programs per discipline with CMG/IMG stream breakdown and description coverage."""

    name = "discipline_summary"
    title = "Discipline Summary"
    description = (
        "Program count by discipline with CMG/IMG stream breakdown "
        "and description coverage percentage."
    )

    def generate(self, session: Session) -> pd.DataFrame:
        rows = session.execute(
            text("""
                SELECT
                    d.name AS discipline,
                    p.stream,
                    p.id AS program_id,
                    CASE WHEN pd.id IS NOT NULL THEN 1 ELSE 0 END AS has_description
                FROM disciplines d
                JOIN programs p ON d.id = p.discipline_id
                LEFT JOIN program_descriptions pd ON p.id = pd.program_id
            """)
        ).fetchall()

        df = pd.DataFrame(rows, columns=["discipline", "stream", "program_id", "has_description"])

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "discipline",
                    "total_programs",
                    "cmg_programs",
                    "img_programs",
                    "description_coverage_pct",
                ]
            )

        # Aggregate by discipline
        summary = (
            df.groupby("discipline")
            .agg(
                total_programs=("program_id", "count"),
                cmg_programs=(
                    "stream",
                    lambda x: (x.str.contains("CMG", case=False, na=False)).sum(),
                ),
                img_programs=(
                    "stream",
                    lambda x: (x.str.contains("IMG", case=False, na=False)).sum(),
                ),
                description_coverage_pct=("has_description", lambda x: round(x.mean() * 100, 1)),
            )
            .reset_index()
        )

        return summary.sort_values("total_programs", ascending=False).reset_index(drop=True)
