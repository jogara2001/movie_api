import sqlalchemy
from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query

from src import database as db

router = APIRouter()


@router.get("/characters/{id}", tags=["characters"])
def get_character(id: int):
    """
    This endpoint returns a single character by its identifier. For each character
    it returns:
    * `character_id`: the internal id of the character. Can be used to query the
      `/characters/{character_id}` endpoint.
    * `character`: The name of the character.
    * `movie`: The movie the character is from.
    * `gender`: The gender of the character.
    * `top_conversations`: A list of characters that the character has the most
      conversations with. The characters are listed in order of the number of
      lines together. These conversations are described below.

    Each conversation is represented by a dictionary with the following keys:
    * `character_id`: the internal id of the character.
    * `character`: The name of the character.
    * `gender`: The gender of the character.
    * `number_of_lines_together`: The number of lines the character has with the
      originally queried character.
    """
    json = None

    stmt1 = (
        sqlalchemy.select(
            db.characters.c.character_id,
            db.characters.c.name,
            db.movies.c.title,
            db.characters.c.gender,
        )
        .select_from(
            db.characters.join(db.movies)
        )
        .where(
            db.characters.c.character_id == id
        )
    )

    # gets conversation_id | character_id for all convos with id
    conversations_shared = (
        sqlalchemy.select(
            db.conversations.c.conversation_id,
            db.conversations.c.character1_id.label("character_id")
        )
        .where(
            db.conversations.c.character2_id == id
        )
        .group_by(
            db.conversations.c.conversation_id
        )
        .union(
            sqlalchemy.select(
                db.conversations.c.conversation_id,
                db.conversations.c.character2_id.label("character_id")
            )
            .where(
                db.conversations.c.character1_id == id
            )
            .group_by(
                db.conversations.c.conversation_id
            )
        ).alias()
    )

    lines_shared = (
        sqlalchemy.select(
            conversations_shared.c.character_id,
            db.lines.c.line_id
        )
        .select_from(
            db.lines.join(conversations_shared)
        )
        .group_by(
            db.lines.c.line_id,
            conversations_shared.c.character_id
        ).alias()
    )

    stmt2 = (
        sqlalchemy.select(
            db.characters.c.character_id,
            db.characters.c.name,
            db.characters.c.gender,
            sqlalchemy.func.count(lines_shared.c.character_id).label("number_of_lines_together")
        )
        .select_from(
            db.characters.join(lines_shared)
        )
        .order_by(
            sqlalchemy.desc("number_of_lines_together")
        )
        .group_by(
            db.characters.c.character_id
        )
    )



    with db.engine.connect() as conn:
        character_result = conn.execute(stmt1).fetchone()
        if character_result is None:
            raise HTTPException(status_code=404, detail="movie not found.")

        conversations_result = conn.execute(stmt2)
        top_conversations = []
        for character in conversations_result:
            top_conversations.append({
                "character_id": character.character_id,
                "character": character.name,
                "gender": character.gender,
                "number_of_lines_together": character.number_of_lines_together
            })
        json = {
            "character_id": character_result.character_id,
            "character": character_result.name,
            "movie": character_result.title,
            "gender": character_result.gender,
            "top_conversations": top_conversations
        }

    return json


class character_sort_options(str, Enum):
    character = "character"
    movie = "movie"
    number_of_lines = "number_of_lines"


@router.get("/characters/", tags=["characters"])
def list_characters(
        name: str = "",
        limit: int = Query(50, ge=1, le=250),
        offset: int = Query(0, ge=0),
        sort: character_sort_options = character_sort_options.character,
):
    """
    This endpoint returns a list of characters. For each character it returns:
    * `character_id`: the internal id of the character. Can be used to query the
      `/characters/{character_id}` endpoint.
    * `character`: The name of the character.
    * `movie`: The movie the character is from.
    * `number_of_lines`: The number of lines the character has in the movie.

    You can filter for characters whose name contains a string by using the
    `name` query parameter.

    You can also sort the results by using the `sort` query parameter:
    * `character` - Sort by character name alphabetically.
    * `movie` - Sort by movie title alphabetically.
    * `number_of_lines` - Sort by number of lines, highest to lowest.

    The `limit` and `offset` query
    parameters are used for pagination. The `limit` query parameter specifies the
    maximum number of results to return. The `offset` query parameter specifies the
    number of results to skip before returning results.
    """
    if sort is character_sort_options.character:
        order_by = db.characters.c.name
    elif sort is character_sort_options.movie:
        order_by = db.movies.c.title
    elif sort is character_sort_options.number_of_lines:
        order_by = sqlalchemy.desc("number_of_lines")
    else:
        assert False

    stmt = (
        sqlalchemy.select(
            db.characters.c.character_id,
            db.characters.c.name,
            sqlalchemy.func.count(db.lines.c.character_id).label("number_of_lines"),
            db.movies.c.title,
        )
        .select_from(db.characters.join(db.lines).join(db.movies))
        .limit(limit)
        .offset(offset)
        .order_by(order_by, db.characters.c.character_id)
        .group_by(
            db.characters.c.character_id,
            db.movies.c.title
        )
    )

    # filter only if name parameter is passed
    if name != "":
        stmt = stmt.where(db.characters.c.name.ilike(f"%{name}%"))

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        json = []
        for row in result:
            json.append(
                {
                    "character_id": row.character_id,
                    "character": row.name,
                    "movie": row.title,
                    "number_of_lines": row.number_of_lines
                }
            )

    return json
