from fastapi.testclient import TestClient

from src.api.server import app

import json

client = TestClient(app)


def test_set_conversation():
    inputJson = {
        "character_1_id": 0,
        "character_2_id": 1,
        "lines": [
            {
                "character_id": 0,
                "line_text": "testing the api"
            }
        ]
    }
    convo_response = client.post("/movies/0/conversations/", json=inputJson)
    assert convo_response.status_code == 200

    get_response = client.get("/conversations/" + str(convo_response.json()))

    assert get_response.json() == {
        'conversation_id': convo_response.json(),
        'lines': [{'character_name': 'BIANCA', 'line': 'testing the api'}],
        'movie_id': 0,
        'movie_title': '10 things i hate about you'
    }


def test_invalid_movie():
    inputJson = {
        "character_1_id": 0,
        "character_2_id": 1,
        "lines": [
            {
                "character_id": 0,
                "line_text": "testing the api"
            }
        ]
    }
    response = client.post("/movies/12346513245/conversations/", json=inputJson)
    assert response.status_code == 404


def test_invalid_character():
    inputJson = {
        "character_1_id": 12345788909,
        "character_2_id": 1,
        "lines": [
            {
                "character_id": 0,
                "line_text": "testing the api"
            }
        ]
    }

    response = client.post("/movies/0/conversations/", json=inputJson)
    assert response.status_code == 404


def test_get_conversation():
    response = client.get("/conversations/25")
    assert response.status_code == 200

    with open("test/lines/conversation-25",
              encoding="utf-8") as f:
        assert response.json() == json.load(f)
