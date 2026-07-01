def test_create_note(client, api_key):
    headers = {"X-API-Key": api_key}
    payload = {"title": "Test Note", "content": "Hello **world**"}
    response = client.post("/api/notes", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Test Note"
    assert data["content"] == "Hello **world**"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_notes_empty(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.get("/api/notes", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_list_notes_with_data(client, api_key):
    headers = {"X-API-Key": api_key}
    client.post("/api/notes", json={"title": "A", "content": "A"}, headers=headers)
    client.post("/api/notes", json={"title": "B", "content": "B"}, headers=headers)
    response = client.get("/api/notes", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2


def test_get_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Test", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.get(f"/api/notes/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test"


def test_get_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.get("/api/notes/999", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}


def test_update_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Original", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.put(
        f"/api/notes/{created['id']}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Updated"
    assert data["content"] == "Body"


def test_update_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.put("/api/notes/999", json={"title": "X"}, headers=headers)
    assert response.status_code == 404


def test_delete_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "To Delete", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.delete(f"/api/notes/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}}
    get_response = client.get(f"/api/notes/{created['id']}", headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.delete("/api/notes/999", headers=headers)
    assert response.status_code == 404


def test_create_note_empty_title(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.post(
        "/api/notes", json={"title": "", "content": "Body"}, headers=headers
    )
    assert response.status_code == 201
    assert response.json()["data"]["title"] == ""


def test_partial_update(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Original", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.put(
        f"/api/notes/{created['id']}",
        json={"content": "New body only"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Original"
    assert data["content"] == "New body only"
