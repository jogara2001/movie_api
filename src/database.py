import array
import csv
import time

from src.datatypes import Character, Movie, Conversation, Line
import os
import io
from supabase import Client, create_client
import dotenv

# DO NOT CHANGE THIS TO BE HARDCODED. ONLY PULL FROM ENVIRONMENT VARIABLES.
dotenv.load_dotenv()
supabase_api_key = os.environ.get("SUPABASE_API_KEY")
supabase_url = os.environ.get("SUPABASE_URL")

if supabase_api_key is None or supabase_url is None:
    raise Exception(
        "You must set the SUPABASE_API_KEY and SUPABASE_URL environment variables."
    )

supabase: Client = create_client(supabase_url, supabase_api_key)

sess = supabase.auth.get_session()

global last_synced
global movies
global characters
global conversations
global lines


def sync_if_needed():
    # This is a hacky way to track if the cached data is in sync.
    # After every write update the "lastUpdated.txt" to the current ns since epoch
    # Upon each api call check the lastUpdated time and compare with the last synced time
    # If synced < updated then we need to resync
    #
    # This could also be more logically implemented using the update times included on the files
    # but because of the overlapping values in different files, I didn't want to set it up.
    # This means that this isn't particularly efficient because everytime a single field is updated,
    # the lambda completely re-runs the entire sync function. It's gross but better than nothing
    #
    global last_synced
    last_updated = (
        supabase.storage.from_("movie-api")
        .download("lastUpdated.txt")
        .decode("utf-8")
    )
    if last_synced <= int(last_updated):
        sync_from_database()


def conversations_write_back(conversation: Conversation, lines: array):
    conversations_csv = (
        supabase.storage.from_("movie-api")
        .download("conversations.csv")
        .decode("utf-8")
    )
    lines_csv = (
        supabase.storage.from_("movie-api")
        .download("lines.csv")
        .decode("utf-8")
    )

    conversation_csv_string = io.StringIO()
    conversation_writer = csv.writer(conversation_csv_string)
    conversation_writer.writerow([
        conversation.id,
        conversation.character1_id,
        conversation.character2_id,
        conversation.movie_id
    ])
    conversations_csv += conversation_csv_string.getvalue()

    line_csv_string = io.StringIO()
    line_writer = csv.writer(line_csv_string)
    for line in lines:
        line_writer.writerow([
            line.id,
            line.character_id,
            line.movie_id,
            line.conversation_id,
            line.line_sort,
            line.line_text
        ])
    lines_csv += line_csv_string.getvalue()

    supabase.storage.from_("movie-api").upload(
        "conversations.csv",
        bytes(conversations_csv, "utf-8"),
        {"x-upsert": "true"},
    )
    supabase.storage.from_("movie-api").upload(
        "lines.csv",
        bytes(lines_csv, "utf-8"),
        {"x-upsert": "true"},
    )

    supabase.storage.from_("movie-api").upload(
        "lastUpdated.txt",
        bytes(str(time.time_ns()), "utf-8"),
        {"x-upsert": "true"},
    )


def try_parse(type, val):
    try:
        return type(val)
    except ValueError:
        return None


# noinspection PyTypeChecker
def sync_from_database():
    movies_csv = (
        supabase.storage.from_("movie-api")
        .download("movies.csv")
        .decode("utf-8")
    )

    characters_csv = (
        supabase.storage.from_("movie-api")
        .download("characters.csv")
        .decode("utf-8")
    )

    conversations_csv = (
        supabase.storage.from_("movie-api")
        .download("conversations.csv")
        .decode("utf-8")
    )

    lines_csv = (
        supabase.storage.from_("movie-api")
        .download("lines.csv")
        .decode("utf-8")
    )
    global movies
    global characters
    global conversations
    global lines
    global last_synced
    movies = {}
    characters = {}
    conversations = {}
    lines = {}

    for row in csv.DictReader(io.StringIO(movies_csv), skipinitialspace=True):
        movie = Movie(
            id=try_parse(int, row["movie_id"]),
            title=row["title"] or None,
            year=row["year"],
            imdb_rating=try_parse(float, row["imdb_rating"]),
            imdb_votes=try_parse(int, row["imdb_votes"]),
            raw_script_url=row["raw_script_url"] or None,
            conversation_ids=[],
            character_ids=[]
        )
        movies[movie.id] = movie

    for row in csv.DictReader(io.StringIO(characters_csv), skipinitialspace=True):
        character = Character(
            id=try_parse(int, row["character_id"]),
            name=row["name"] or None,
            movie_id=try_parse(int, row["movie_id"]),
            gender=row["gender"] or None,
            age=try_parse(int, row["age"]),
            line_ids=[],
            conversation_ids=[]
        )
        characters[character.id] = character
        movies[character.movie_id].character_ids.append(character.id)

    for row in csv.DictReader(io.StringIO(conversations_csv), skipinitialspace=True):
        conversation = Conversation(
            id=try_parse(int, row["conversation_id"]),
            character1_id=try_parse(int, row["character1_id"]),
            character2_id=try_parse(int, row["character2_id"]),
            movie_id=try_parse(int, row["movie_id"]),
            line_ids=[],
        )
        conversations[conversation.id] = conversation
        movies[conversation.movie_id].conversation_ids.append(conversation.id)
        characters[conversation.character1_id].conversation_ids.append(conversation.id)
        characters[conversation.character2_id].conversation_ids.append(conversation.id)

    for row in csv.DictReader(io.StringIO(lines_csv), skipinitialspace=True):
        line = Line(
            id=try_parse(int, row["line_id"]),
            character_id=try_parse(int, row["character_id"]),
            movie_id=try_parse(int, row["movie_id"]),
            conversation_id=try_parse(int, row["conversation_id"]),
            line_sort=try_parse(int, row["line_sort"]),
            line_text=row["line_text"],
        )
        lines[line.id] = line
        characters[line.character_id].line_ids.append(line.id)
        conversations[line.conversation_id].line_ids.append(line.id)

    last_synced = time.time_ns()


sync_from_database()
