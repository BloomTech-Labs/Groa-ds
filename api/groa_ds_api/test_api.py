from fastapi.testclient import TestClient
from groa_ds_api import create_app

application = create_app()
client = TestClient(application)


def test_index():
    response = client.get("/")
    assert response.status_code == 200


def test_wrong_method():
    response = client.post("/", json={"message": "testing"})
    assert response.status_code == 405


def test_recommendations():
    payload = {
        "user_id": 11,
        "num_recs": 50,
        "good_threshold": 5,
        "bad_threshold": 4,
        "harshness": 1
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200


def test_service_providers():
    response = client.get("/service-providers/0111161")
    assert response.status_code == 200
