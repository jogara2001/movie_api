from uuid import uuid4

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

    # There are some serious race condition concerns here. If there's a write any time
    # after the sync but before this function finishes, it could cause issues. With this
    # implementation that means that the first write would be removed. There are also some
    # more drawbacks detailed in database.py
    # This implementation only really works for a few clients making few write calls
    db.sync_if_needed()

    if movie_id not in db.movies:
        raise HTTPException(status_code=404, detail="movie not found.")
    if conversation.character_1_id not in db.characters or db.characters[conversation.character_1_id].movie_id != movie_id:
        raise HTTPException(status_code=404, detail="character 1 not found.")
    if conversation.character_2_id not in db.characters or db.characters[conversation.character_2_id].movie_id != movie_id:
        raise HTTPException(status_code=404, detail="character 2 not found.")


    convo = Conversation(
        id=uuid4().int,
        character1_id=conversation.character_1_id,
        character2_id=conversation.character_2_id,
        movie_id=movie_id,
        line_ids=[]
    )
    lines = []
    line_sort = 0
    for line in conversation.lines:
        newLine = Line(
            id=uuid4().int,
            character_id=line.character_id,
            movie_id=movie_id,
            conversation_id=convo.id,
            line_sort=line_sort,
            line_text=line.line_text
        )
        lines.append(newLine)
        db.lines[newLine.id] = newLine
        convo.line_ids.append(newLine.id)
        line_sort += 1
    db.conversations[convo.id] = convo
    db.conversations_write_back(convo, lines)

    return convo.id

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
    json = None
    lines = []

    if id in db.conversations:
        conversation = db.conversations[id]
        for line_id in conversation.line_ids:
            lines.append({
                'character_name': db.characters[db.lines[line_id].character_id].name,
                'line': db.lines[line_id].line_text
            })
        json = {
            "conversation_id": id,
            "movie_id": conversation.movie_id,
            "movie_title": db.movies[conversation.movie_id].title,
            "lines": lines
        }

    if json is None:
        raise HTTPException(status_code=404, detail="conversation not found.")
    return json
