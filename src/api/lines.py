import sqlalchemy
from fastapi import APIRouter, HTTPException
from fastapi.params import Query
from src import database as db

router = APIRouter()


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

    stmt = (
        sqlalchemy.select(
            db.lines.c.line_id,
            db.movies.c.title,
            db.lines.c.conversation_id,
            db.lines.c.line_text,
            db.characters.c.name
        )
        .select_from(
            db.lines
            .join(db.movies, db.movies.c.movie_id == db.lines.c.movie_id)
            .join(db.characters, db.characters.c.character_id == db.lines.c.character_id)
            .join(db.conversations, db.conversations.c.conversation_id == db.lines.c.conversation_id))
        .where(
            db.lines.c.line_id == id
        )
    )

    with db.engine.connect() as conn:
        result = conn.execute(stmt).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="line not found.")
        return {
            "movie": result.title,
            "spoken_by": result.name,
            # "spoken_to": result.other_character,
            "conversation_id": result.conversation_id,
            "line": result.line_text

        }


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
    stmt = (
        sqlalchemy.select(
            db.lines.c.line_id,
            db.movies.c.title,
            db.lines.c.line_text,
            db.characters.c.name
        )
        .select_from(db.lines.join(db.characters).join(db.movies))
        .limit(limit)
        .offset(offset)
        .order_by(db.lines.c.line_id, db.lines.c.line_sort)
        .group_by(
            db.lines.c.line_id,
            db.movies.c.title,
            db.characters.c.name,
            db.lines.c.line_text
        )
    )

    # filter only if name parameter is passed
    if character != "":
        stmt = stmt.where(db.characters.c.name.ilike(f"%{character}%"))
    if movie != "":
        stmt = stmt.where(db.movies.c.title.ilike(f"%{movie}%"))

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        json = []
        for row in result:
            json.append(
                {
                    "movie_title": row.title,
                    "character_name": row.name,
                    "line": row.line_text,
                }
            )

    return json
