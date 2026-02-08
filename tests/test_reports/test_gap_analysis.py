"""Tests for program gap analysis report."""

from carms.reports.program_gap_analysis import ProgramGapAnalysisReport


def test_generate_returns_discipline_and_coverage(session, sample_program):
    report = ProgramGapAnalysisReport()
    df = report.generate(session)
    assert "discipline" in df.columns
    assert "coverage_pct" in df.columns
    assert "schools_offering" in df.columns
    assert "total_schools" in df.columns
    assert len(df) >= 1


def test_coverage_is_percentage(session, sample_program):
    report = ProgramGapAnalysisReport()
    df = report.generate(session)
    for _, row in df.iterrows():
        assert 0 <= row["coverage_pct"] <= 100
