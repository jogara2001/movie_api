from uuid import uuid4

import sqlalchemy
from fastapi import APIRouter, HTTPException
from src import database as db
from pydantic import BaseModel
from typing import List
from datetime import datetime

from src.datatypes import Conversation, Line


# FastAPI is inferring what the request body should look like
# based on the following two classes.
class LinesJson(BaseModel):
    character_id: int
    line_text: str


class ConversationJson(BaseModel):
    character_1_id: int
    character_2_id: int
    lines: List[LinesJson]


router = APIRouter()


@router.post("/movies/{movie_id}/conversations/", tags=["movies"])
def add_conversation(movie_id: int, conversation: ConversationJson):
    """
    This endpoint adds a conversation to a movie. The conversation is represented
    by the two characters involved in the conversation and a series of lines between
    those characters in the movie.

    The endpoint ensures that all characters are part of the referenced movie,
    that the characters are not the same, and that the lines of a conversation
    match the characters involved in the conversation.

    Line sort is set based on the order in which the lines are provided in the
    request body.

    The endpoint returns the id of the resulting conversation that was created.
    """


@router.get("/conversations/{id}", tags=["lines"])
def get_conversation(id: int):
    """
    This endpoint returns a full conversation. Each conversation includes
    * 'conversation_id': id of the convo
    * 'movie_id': id of the movie
    * 'movie_title': title of the movie
    * 'lines' all the lines in the conversation

    Lines follow this structure
    * 'character_name': the name of the character speaking
    * 'line': the full text of the line
    """
    stmt1 = (
        sqlalchemy.select(
            db.conversations.c.conversation_id,
            db.conversations.c.movie_id,
            db.movies.c.title,
        )
        .select_from(db.conversations.join(db.movies))
        .where(
            db.conversations.c.conversation_id == id
        )
    )

    stmt2 = (
        sqlalchemy.select(
            db.lines.c.line_text,
            db.characters.c.character_id,
            db.characters.c.name
        )
        .select_from(db.lines.join(db.characters))
        .where(
            db.lines.c.conversation_id == id
        )
    )

    with db.engine.connect() as conn:
        result = conn.execute(stmt1).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="conversation not found.")

        lines_result = conn.execute(stmt2)
        all_lines = []
        for line in lines_result:
            all_lines.append({
                "character_name": line.name,
                "line": line.line_text
            })

        return {
            "conversation_id": result.conversation_id,
            "movie_id": result.movie_id,
            "movie_title": result.title,
            "lines": all_lines
        }

