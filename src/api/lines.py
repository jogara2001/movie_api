from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db

router = APIRouter()


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


@router.get("/lines/{id}", tags=["lines"])
def get_line(
        id: int
):
    """
        This endpoint returns a full line. Each line includes
        * 'movie': the movie it's from
        * 'spoken_by': the character that says the line
        * 'spoken_to': the character that is spoken to
        * 'conversation_id': the id of the conversation in which this line takes place
        * 'line': the full text of the line
        """
    if id in db.lines:
        line = db.lines[id]
        spoken_to = db.conversations[line.conversation_id].character2_id
        if spoken_to == line.character_id:
            spoken_to = db.conversations[line.conversation_id].character1_id
        return {
            "movie": db.movies[line.movie_id].title,
            "spoken_by": db.characters[line.character_id].name,
            "spoken_to": db.characters[spoken_to].name,
            "conversation_id": line.conversation_id,
            "line": line.line_text

        }
    else:
        raise HTTPException(status_code=404, detail="line not found")


@router.get("/lines/", tags=["lines"])
def get_lines(
        character: str = "",
        movie: str = "",
        limit: int = Query(50, ge=1, le=250),
        offset: int = Query(0, ge=0),
):
    """
    This endpoint returns a list of lines. For each line it returns:
    * 'movie_title': the title of the movie.
    * 'character_name': the name of the character who said the line
    * 'line': the full text of the line

    This endpoint allows filtering based on the 'movie' or 'character' parameters

    The `limit` and `offset` query
    parameters are used for pagination. The `limit` query parameter specifies the
    maximum number of results to return. The `offset` query parameter specifies the
    number of results to skip before returning results.
    """

    json = []
    if character:
        items = list(
            filter(lambda line: character.upper() in db.characters[line.character_id].name.upper(), db.lines.values()))
    else:
        items = list(db.lines.values())

    if movie:
        items = list(filter(lambda line: movie.upper() in db.movies[line.movie_id].title.upper(), items))

    items = sorted(items, key=lambda line: (line.conversation_id, line.line_sort))

    for line in items[offset: offset + limit]:
        json.append({
            "movie_title": db.movies[line.movie_id].title,
            "character_name": db.characters[line.character_id].name,
            "line": line.line_text
        })

    return json
