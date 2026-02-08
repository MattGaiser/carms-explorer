"""Test disciplines endpoint."""

from carms.db.models import Discipline


def test_list_disciplines_empty(client):
    response = client.get("/disciplines/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_disciplines(client, session):
    session.add(Discipline(id=1, name="Alpha"))
    session.add(Discipline(id=2, name="Beta"))
    session.flush()

    response = client.get("/disciplines/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alpha"
    assert data[0]["program_count"] == 0
