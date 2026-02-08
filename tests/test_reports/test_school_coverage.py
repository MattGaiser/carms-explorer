"""Tests for school coverage report."""

from carms.reports.school_coverage import SchoolCoverageReport


def test_generate_returns_school_and_total(session, sample_program):
    report = SchoolCoverageReport()
    df = report.generate(session)
    assert "school" in df.columns
    assert "total_programs" in df.columns
    assert len(df) >= 1


def test_to_json_structure(session, sample_program):
    report = SchoolCoverageReport()
    result = report.to_json(session)
    assert result["metadata"]["name"] == "school_coverage"
    assert len(result["data"]) >= 1
