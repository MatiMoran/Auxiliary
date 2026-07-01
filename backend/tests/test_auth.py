from app.config import settings


def test_missing_api_key_returns_401(client):
    response = client.get("/api/notes")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}


def test_invalid_api_key_returns_401(client):
    response = client.get("/api/notes", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}


def test_valid_api_key_succeeds(client, api_key):
    response = client.get("/api/notes", headers={"X-API-Key": api_key})
    assert response.status_code == 200


def test_health_endpoint_does_not_require_auth(client):
    response = client.get("/api/health")
    assert response.status_code == 200
