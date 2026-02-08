"""Tests for discipline summary report."""

from carms.reports.discipline_summary import DisciplineSummaryReport


def test_generate_returns_expected_columns(session, sample_program):
    report = DisciplineSummaryReport()
    df = report.generate(session)
    assert "discipline" in df.columns
    assert "total_programs" in df.columns
    assert "cmg_programs" in df.columns
    assert "img_programs" in df.columns
    assert "description_coverage_pct" in df.columns


def test_generate_counts_programs(session, sample_program):
    report = DisciplineSummaryReport()
    df = report.generate(session)
    assert len(df) >= 1
    row = df[df["discipline"] == "Anesthesiology"].iloc[0]
    assert row["total_programs"] >= 1


def test_to_json_returns_metadata_and_data(session, sample_program):
    report = DisciplineSummaryReport()
    result = report.to_json(session)
    assert "metadata" in result
    assert "data" in result
    assert result["metadata"]["name"] == "discipline_summary"
    assert result["metadata"]["row_count"] >= 1
    assert isinstance(result["data"], list)
