from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db

router = APIRouter()


@router.get("/movies/{movie_id}", tags=["movies"])
def get_movie(movie_id: int):
    """
    This endpoint returns a single movie by its identifier. For each movie it returns:
    * `movie_id`: the internal id of the movie.
    * `title`: The title of the movie.
    * `top_characters`: A list of characters that are in the movie. The characters
      are ordered by the number of lines they have in the movie. The top five
      characters are listed.

    Each character is represented by a dictionary with the following keys:
    * `character_id`: the internal id of the character.
    * `character`: The name of the character.
    * `num_lines`: The number of lines the character has in the movie.

    """
    db.sync_if_needed()
    json = None

    if movie_id in db.movies:
        movie = db.movies[movie_id]
        top_characters = []

        sorted_characters = sorted(movie.character_ids, key=lambda chid: len(db.characters[chid].line_ids), reverse=True)
        for character_id in sorted_characters:
            top_characters.append({
                "character_id": character_id,
                "character": db.characters[character_id].name,
                "num_lines": len(db.characters[character_id].line_ids)
            })
            if len(top_characters) >= 5:
                break

        json = {
            "movie_id": movie_id,
            "title": movie.title,
            "top_characters": top_characters
        }

    if json is None:
        raise HTTPException(status_code=404, detail="movie not found.")

    return json


class movie_sort_options(str, Enum):
    movie_title = "movie_title"
    year = "year"
    rating = "rating"


# Add get parameters
@router.get("/movies/", tags=["movies"])
def list_movies(
    name: str = "",
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort: movie_sort_options = movie_sort_options.movie_title,
):
    """
    This endpoint returns a list of movies. For each movie it returns:
    * `movie_id`: the internal id of the movie. Can be used to query the
      `/movies/{movie_id}` endpoint.
    * `movie_title`: The title of the movie.
    * `year`: The year the movie was released.
    * `imdb_rating`: The IMDB rating of the movie.
    * `imdb_votes`: The number of IMDB votes for the movie.

    You can filter for movies whose titles contain a string by using the
    `name` query parameter.

    You can also sort the results by using the `sort` query parameter:
    * `movie_title` - Sort by movie title alphabetically.
    * `year` - Sort by year of release, earliest to latest.
    * `rating` - Sort by rating, highest to lowest.

    The `limit` and `offset` query
    parameters are used for pagination. The `limit` query parameter specifies the
    maximum number of results to return. The `offset` query parameter specifies the
    number of results to skip before returning results.
    """
    db.sync_if_needed()
    json = []
    if name:
        items = list(filter(lambda movie: name.upper() in movie.title.upper(), db.movies.values()))
    else:
        items = list(db.movies.values())

    if sort == movie_sort_options.movie_title:
        items = sorted(items, key=lambda movie: movie.title)
    if sort == movie_sort_options.year:
        items = sorted(items, key=lambda movie: movie.year)
    if sort == movie_sort_options.rating:
        items = sorted(items, key=lambda movie: movie.imdb_rating, reverse=True)

    for movie in items[offset: offset + limit]:
        json.append({
            "movie_id": movie.id,
            "movie_title": movie.title,
            "year": str(movie.year),
            "imdb_rating": movie.imdb_rating,
            "imdb_votes": movie.imdb_votes,
        })

    return json
