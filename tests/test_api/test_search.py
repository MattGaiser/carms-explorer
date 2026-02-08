"""Test search endpoint."""


def test_search_validation(client):
    response = client.post("/search/", json={"query": ""})
    assert response.status_code == 422


def test_search_valid_request(client, sample_program):
    # This test requires embeddings to be present; basic validation test
    response = client.post("/search/", json={"query": "family medicine rural"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert data["query"] == "family medicine rural"
