import random

import sqlalchemy
from fastapi import APIRouter, HTTPException

from src import database as db
from pydantic import BaseModel
from typing import List


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

    The endpoint ensures that:
    - all characters are part of the referenced movie
    - the characters are not the same
    - lines of a conversation match the characters involved in the conversation.

    Line sort is set based on the order in which the lines are provided in the
    request body.

    The endpoint returns the id of the resulting conversation that was created.
    """
    if conversation.character_2_id == conversation.character_1_id:
        raise HTTPException(status_code=400, detail="characters ids cannot be equal")
    for line in conversation.lines:
        if line.character_id != conversation.character_1_id and line.character_id != conversation.character_2_id:
            raise HTTPException(status_code=400, detail="lines don't match characters")

    verify = (
        sqlalchemy.select(
            db.characters.c.movie_id,
            db.characters.c.character_id
        )
        .select_from(db.characters)
        .where(
            db.characters.c.movie_id == movie_id and
            (db.characters.c.character_id == conversation.character_1_id or
             db.characters.c.character_id == conversation.character_2_id)
        )
    )

    last_convo = sqlalchemy.select(
        db.conversations.c.conversation_id
    ).order_by(sqlalchemy.desc(db.conversations.c.conversation_id))

    last_line = sqlalchemy.select(
        db.lines.c.line_id
    ).order_by(sqlalchemy.desc(db.lines.c.line_id))

    convo_id = 1
    next_line_id = 1

    with db.engine.connect() as conn:
        convo = conn.execute(last_convo).fetchone()
        line = conn.execute(last_line).fetchone()
        convo_id += convo.conversation_id
        next_line_id += line.line_id



    conversation_insert = db.conversations.insert().values(
        conversation_id=convo_id,
        character1_id=conversation.character_1_id,
        character2_id=conversation.character_2_id,
        movie_id=movie_id
    )

    lines_statements = []
    line_sort = 1
    for line in conversation.lines:
        lines_statements.append(db.lines.insert().values(
            line_id=next_line_id,
            character_id=line.character_id,
            movie_id=movie_id,
            conversation_id=convo_id,
            line_sort=line_sort,
            line_text=line.line_text
        ))
        line_sort += 1
        next_line_id += 1

    with db.engine.connect() as conn:
        result = conn.execute(verify).fetchall()
        if len(result) < 2:
            raise HTTPException(status_code=400, detail=f"1 or more characters not in movie")
        conn.execute(conversation_insert)
        for line_statement in lines_statements:
            conn.execute(line_statement)
        conn.commit()

    return convo_id


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
