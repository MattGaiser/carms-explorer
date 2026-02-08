"""Dagster assets for pandas-based reports."""

import json

from dagster import AssetExecutionContext, AssetIn, asset

from carms.etl.resources import DatabaseResource


@asset(
    group_name="reports",
    ins={"stg_descriptions": AssetIn()},
    compute_kind="pandas",
)
def report_discipline_summary(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_descriptions: int,
) -> str:
    """Generate discipline summary report with stream breakdown."""
    from carms.reports.discipline_summary import DisciplineSummaryReport

    report = DisciplineSummaryReport()
    with database.get_session() as session:
        result = report.to_json(session)
    context.log.info(f"Discipline summary: {result['metadata']['row_count']} rows")
    return json.dumps(result["metadata"])


@asset(
    group_name="reports",
    ins={"stg_descriptions": AssetIn()},
    compute_kind="pandas",
)
def report_school_coverage(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_descriptions: int,
) -> str:
    """Generate school coverage matrix report."""
    from carms.reports.school_coverage import SchoolCoverageReport

    report = SchoolCoverageReport()
    with database.get_session() as session:
        result = report.to_json(session)
    context.log.info(f"School coverage: {result['metadata']['row_count']} rows")
    return json.dumps(result["metadata"])


@asset(
    group_name="reports",
    ins={"stg_descriptions": AssetIn()},
    compute_kind="pandas",
)
def report_program_gap_analysis(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_descriptions: int,
) -> str:
    """Generate program gap analysis report."""
    from carms.reports.program_gap_analysis import ProgramGapAnalysisReport

    report = ProgramGapAnalysisReport()
    with database.get_session() as session:
        result = report.to_json(session)
    context.log.info(f"Gap analysis: {result['metadata']['row_count']} rows")
    return json.dumps(result["metadata"])
