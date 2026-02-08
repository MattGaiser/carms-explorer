"""Tests for reports API endpoints."""


def test_list_reports(client):
    """GET /reports/ returns available reports."""
    response = client.get("/reports/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    names = [r["name"] for r in data]
    assert "discipline_summary" in names
    assert "school_coverage" in names
    assert "program_gap_analysis" in names


def test_generate_discipline_summary(client, sample_program):
    """GET /reports/discipline_summary returns JSON with metadata + data."""
    response = client.get("/reports/discipline_summary")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "data" in data
    assert data["metadata"]["name"] == "discipline_summary"
    assert data["metadata"]["row_count"] >= 1


def test_generate_school_coverage(client, sample_program):
    """GET /reports/school_coverage returns valid report."""
    response = client.get("/reports/school_coverage")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["name"] == "school_coverage"


def test_generate_gap_analysis(client, sample_program):
    """GET /reports/program_gap_analysis returns valid report."""
    response = client.get("/reports/program_gap_analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["name"] == "program_gap_analysis"


def test_nonexistent_report_returns_404(client):
    """GET /reports/nonexistent returns 404."""
    response = client.get("/reports/nonexistent")
    assert response.status_code == 404
