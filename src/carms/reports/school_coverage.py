"""School coverage report — discipline coverage matrix by school."""

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from carms.reports.base import BaseReport


class SchoolCoverageReport(BaseReport):
    """Discipline coverage matrix with school as index and discipline as columns."""

    name = "school_coverage"
    title = "School Coverage"
    description = (
        "Pivot table showing program counts by school and discipline, "
        "with total programs per school."
    )

    def generate(self, session: Session) -> pd.DataFrame:
        rows = session.execute(
            text("""
                SELECT s.name AS school, d.name AS discipline, COUNT(p.id) AS programs
                FROM programs p
                JOIN schools s ON p.school_id = s.id
                JOIN disciplines d ON p.discipline_id = d.id
                GROUP BY s.name, d.name
            """)
        ).fetchall()

        df = pd.DataFrame(rows, columns=["school", "discipline", "programs"])

        if df.empty:
            return pd.DataFrame(columns=["school", "total_programs"])

        pivot = pd.pivot_table(
            df,
            values="programs",
            index="school",
            columns="discipline",
            fill_value=0,
            aggfunc="sum",
        )

        # Add total column
        pivot["total_programs"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total_programs", ascending=False)

        # Flatten: move school from index to column
        result = pivot.reset_index()
        return result
