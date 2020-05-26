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
        "user_id": "11",
        "num_recs": 50,
        "good_threshold": 5,
        "bad_threshold": 4,
        "harshness": 1
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200


def test_recommendations_interaction():
    response = client.get("/recommendations/interaction/00ubmnwy5j5shXUQY4x6/0200720")
    assert response.status_code == 200


def test_search():
    payload = {
        "query": "lord"
    }
    response = client.post("/search", json=payload)
    assert response.status_code == 200


def test_rating():
    payload = {
        "user_id": "00ubmnwy5j5shXUQY4x6",
        "movie_id": "0181865",
        "rating": 5.0
    }
    response = client.post("/rating", json=payload)
    assert response.status_code == 200
    payload["rating"] = 4.5
    response = client.post("/rating", json=payload)
    assert response.status_code == 200


def test_watchlist():
    payload = {
        "user_id": "00ubmnwy5j5shXUQY4x6",
        "movie_id": "0200720"
    }
    response = client.post("/watchlist", json=payload)
    assert response.status_code == 200
    response = client.post("/watchlist/"+payload["user_id"]+"/remove/"+payload["movie_id"])
    assert response.status_code == 200


def test_notwatchlist():
    payload = {
        "user_id": "00ubmnwy5j5shXUQY4x6",
        "movie_id": "0200720"
    }
    response = client.post("/notwatchlist", json=payload)
    assert response.status_code == 200
    response = client.post("/notwatchlist/"+payload["user_id"]+"/remove/"+payload["movie_id"])
    assert response.status_code == 200


def test_similar_movies():
    payload = {
        "movie_id": "0181875",
        "num_movies": 100
    }
    response = client.post("/similar-movies", json=payload)
    assert response.status_code == 200


def test_service_providers():
    response = client.get("/service-providers/0171580")
    assert response.status_code == 200


def test_explore():
    response = client.get("/explore")
    assert response.status_code == 200


def test_explore_user():
    response = client.get("/explore/00ubmnwy5j5shXUQY4x6")
    assert response.status_code == 200


def test_movie_lists():
    payload = {
        "user_id": "00ubmnwy5j5shXUQY4x6",
        "name": "Tester List",
        "private": False
    }
    response = client.post("/movie-list", json=payload)
    list_id = str(response.json()["list_id"])
    assert response.status_code == 200

    response = client.put("/movie-list/" + list_id + "/add/9265856")
    assert response.status_code == 200

    response = client.get("/movie-list/" + list_id)
    assert response.status_code == 200

    response = client.put("/movie-list/" + list_id + "/remove/9265856")
    assert response.status_code == 200

    response = client.delete("/movie-list/" + list_id)
    assert response.status_code == 200


def test_get_all_lists():
    response = client.get("/movie-list/all")
    assert response.status_code == 200


def test_get_user_lists():
    response = client.get("/movie-list/all/00ubmnwy5j5shXUQY4x6")
    assert response.status_code == 200