from fastapi.testclient import TestClient
from groa_ds_api import create_app

application = create_app()
client = TestClient(application)


def test_scraper():
    payload = {
        "start": 0,
        "end": 5
    }
    response = client.post("/scrape", json=payload)
    assert response.status_code == 200

def test_scraper_update():
    payload = {
        "start": 0,
        "end": 5
    }
    response = client.post("/scrape-update", json=payload)
    assert response.status_code == 200
