import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from Api import app  # Убедись, что путь правильный

client = TestClient(app)

TEST_JWT = "fake.jwt.token"
TEST_COOKIE = {"token": TEST_JWT}

def test_create_post_unauthorized():
    response = client.post("/posts", json={
        "name": "Unauthorized",
        "desc": "You shall not pass!",
        "tags": ["unauth"]
    })
    assert response.status_code == 401
    assert "Token not found" in response.json()["detail"]

def test_get_nonexistent_post():
    non_existent_id = str(uuid4())
    response = client.get(f"/posts/{non_existent_id}")
    assert response.status_code in (404, 500)

def test_get_posts_by_user_empty():
    user_id = str(uuid4())
    response = client.get(f"/posts/user/{user_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

