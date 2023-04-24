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
    db.sync_if_needed()
    json = None

    if id in db.characters:
        character = db.characters[id]
        top_conversations = dict()
        for conversation_id in character.conversation_ids:
            other_character_id = db.conversations[conversation_id].character1_id
            if other_character_id == id:
                other_character_id = db.conversations[conversation_id].character2_id

            lines = dict(filter(lambda line: line[1].conversation_id == conversation_id, db.lines.items()))
            if other_character_id in top_conversations:
                # Already exists
                top_conversations[other_character_id]["number_of_lines_together"] += len(lines)
            else:
                # New
                top_conversations[other_character_id] = {
                    "character_id": other_character_id,
                    "character": db.characters[other_character_id].name,
                    "gender": db.characters[other_character_id].gender,
                    "number_of_lines_together": len(lines)
                }

        json = {
            "character_id": id,
            "character": character.name,
            "movie": db.movies[character.movie_id].title,
            "gender": character.gender,
            "top_conversations": sorted(top_conversations.values(), key=lambda d: d['number_of_lines_together'],
                                        reverse=True)
        }

    if json is None:
        raise HTTPException(status_code=404, detail="character not found.")
    else:
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
    db.sync_if_needed()
    json = []
    if name:
        items = list(filter(lambda character: name.upper() in character.name.upper(), db.characters.values()))
    else:
        items = list(db.characters.values())

    if sort == character_sort_options.character:
        items = sorted(items, key=lambda character: character.name)
    if sort == character_sort_options.movie:
        items = sorted(items, key=lambda character: db.movies[character.movie_id].title)
    if sort == character_sort_options.number_of_lines:
        items = sorted(items, key=lambda character: len(character.line_ids), reverse=True)

    for character in items[offset: offset + limit]:
        json.append({
            "character_id": character.id,
            "character": character.name,
            "movie": db.movies[character.movie_id].title,
            "number_of_lines": len(character.line_ids)
        })

    return json
