from dataclasses import dataclass


@dataclass
class Character:
    id: int
    name: str
    movie_id: int
    gender: str
    age: int
    line_ids: []
    conversation_ids: []


@dataclass
class Movie:
    id: int
    title: str
    year: str
    imdb_rating: float
    imdb_votes: int
    raw_script_url: str
    conversation_ids: []
    character_ids: []


@dataclass
class Conversation:
    id: int
    character1_id: int
    character2_id: int
    movie_id: int
    line_ids: []


@dataclass
class Line:
    id: int
    character_id: int
    movie_id: int
    conversation_id: int
    line_sort: int
    line_text: str
