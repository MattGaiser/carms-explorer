"""Test analytics endpoints."""


def test_analytics_overview(client, sample_program):
    response = client.get("/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_programs"] >= 1
    assert data["total_disciplines"] >= 1
    assert data["total_schools"] >= 1


def test_analytics_disciplines(client, sample_program):
    response = client.get("/analytics/disciplines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["discipline"] == "Anesthesiology"


def test_analytics_schools(client, sample_program):
    response = client.get("/analytics/schools")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
