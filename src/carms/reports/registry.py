"""Report registry — discover and look up available reports."""

from carms.reports.base import BaseReport
from carms.reports.discipline_summary import DisciplineSummaryReport
from carms.reports.program_gap_analysis import ProgramGapAnalysisReport
from carms.reports.school_coverage import SchoolCoverageReport

REPORTS: dict[str, BaseReport] = {
    "discipline_summary": DisciplineSummaryReport(),
    "school_coverage": SchoolCoverageReport(),
    "program_gap_analysis": ProgramGapAnalysisReport(),
}


def get_report(name: str) -> BaseReport | None:
    """Look up a report by name."""
    return REPORTS.get(name)


def list_reports() -> list[dict]:
    """Return metadata for all registered reports."""
    return [
        {"name": r.name, "title": r.title, "description": r.description} for r in REPORTS.values()
    ]
