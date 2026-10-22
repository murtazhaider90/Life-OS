from fastapi.testclient import TestClient
from app.main import app


def test_homepage_renders():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Personal AI Life OS" in response.text
