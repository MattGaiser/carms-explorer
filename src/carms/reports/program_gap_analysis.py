"""Program gap analysis report — identify missing disciplines per school."""

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from carms.reports.base import BaseReport


class ProgramGapAnalysisReport(BaseReport):
    """Identify disciplines missing at each school, with per-discipline coverage percentage."""

    name = "program_gap_analysis"
    title = "Program Gap Analysis"
    description = (
        "Per-discipline coverage across schools: how many schools offer each discipline "
        "and the coverage percentage."
    )

    def generate(self, session: Session) -> pd.DataFrame:
        rows = session.execute(
            text("""
                SELECT s.name AS school, d.name AS discipline
                FROM programs p
                JOIN schools s ON p.school_id = s.id
                JOIN disciplines d ON p.discipline_id = d.id
            """)
        ).fetchall()

        df = pd.DataFrame(rows, columns=["school", "discipline"])

        if df.empty:
            return pd.DataFrame(
                columns=["discipline", "schools_offering", "total_schools", "coverage_pct"]
            )

        total_schools = df["school"].nunique()

        # Cross-tabulation of school × discipline presence
        ct = pd.crosstab(df["school"], df["discipline"])
        # Convert counts to boolean presence
        presence = ct > 0

        # Per-discipline: how many schools offer it
        discipline_coverage = presence.sum(axis=0).reset_index()
        discipline_coverage.columns = ["discipline", "schools_offering"]
        discipline_coverage["total_schools"] = total_schools
        discipline_coverage["coverage_pct"] = round(
            discipline_coverage["schools_offering"] / total_schools * 100, 1
        )

        return discipline_coverage.sort_values("coverage_pct", ascending=False).reset_index(
            drop=True
        )
