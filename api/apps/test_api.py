from fastapi.testclient import TestClient
from apps import create_app

application = create_app()
client = TestClient(application)


def test_index():
    response = client.get("/")
    assert response.status_code == 200


def test_wrong_method():
    response = client.post("/", json={"message": "testing"})
    assert response.status_code == 405

def test_decades():
    response = client.get("/stats/decades/1")
    assert response.status_code == 200
