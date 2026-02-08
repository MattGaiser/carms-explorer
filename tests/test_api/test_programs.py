"""Test programs endpoints."""


def test_list_programs_empty(client):
    response = client.get("/programs/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_programs(client, sample_program):
    response = client.get("/programs/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == sample_program.name


def test_filter_by_discipline(client, sample_program):
    response = client.get(f"/programs/?discipline_id={sample_program.discipline_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_no_results(client, sample_program):
    response = client.get("/programs/?discipline_id=9999")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_program_detail(client, sample_program):
    response = client.get(f"/programs/{sample_program.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_program.name
    assert data["discipline"] == "Anesthesiology"


def test_get_program_not_found(client):
    response = client.get("/programs/99999")
    assert response.status_code == 404
