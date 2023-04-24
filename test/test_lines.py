from fastapi.testclient import TestClient

from src.api.server import app

import json

client = TestClient(app)


def test_get_conversation():
    response = client.get("/conversations/25")
    assert response.status_code == 200

    with open("test/lines/conversation-25",
              encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_lines_movie_character_filter():
    response = client.get("/lines/?movie=watchmen&character=dr. manhattan")
    assert response.status_code == 200

    with open("test/lines/lines-character=dr. manhattan&movie=watchmen.json",
              encoding="utf-8",
              ) as f:
        assert response.json() == json.load(f)

def test_get_line():
    response = client.get("/lines/49")
    assert response.status_code == 200

    with open("test/lines/lines-49", encoding="utf-8") as f:
        assert response.json() == json.load(f)

def test_404():
    response = client.get("/conversation/400")
    assert response.status_code == 404
