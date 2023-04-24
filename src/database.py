import csv
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

# TODO: Below is purely an example of reading and then writing a csv from supabase.
# You should delete this code for your working example.

# START PLACEHOLDER CODE
#
# # Reading in the log file from the supabase bucket
# log_csv = (
#     supabase.storage.from_("movie-api")
#     .download("movie_conversations_log.csv")
#     .decode("utf-8")
# )
#
# logs = []
# for row in csv.DictReader(io.StringIO(log_csv), skipinitialspace=True):
#     logs.append(row)
#
#
# # Writing to the log file and uploading to the supabase bucket
# def upload_new_log():
#     output = io.StringIO()
#     csv_writer = csv.DictWriter(
#         output, fieldnames=["post_call_time", "movie_id_added_to"]
#     )
#     csv_writer.writeheader()
#     csv_writer.writerows(logs)
#     supabase.storage.from_("movie-api").upload(
#         "movie_conversations_log.csv",
#         bytes(output.getvalue(), "utf-8"),
#         {"x-upsert": "true"},
#     )
#

# END PLACEHOLDER CODE


def try_parse(type, val):
    try:
        return type(val)
    except ValueError:
        return None


with open("movies.csv", mode="r", encoding="utf8") as csv_file:
    movies = {}
    for row in csv.DictReader(csv_file, skipinitialspace=True):
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

with open("characters.csv", mode="r", encoding="utf8") as csv_file:
    characters = {}
    for row in csv.DictReader(csv_file, skipinitialspace=True):
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


with open("conversations.csv", mode="r", encoding="utf8") as csv_file:
    conversations = {}
    for row in csv.DictReader(csv_file, skipinitialspace=True):
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

with open("lines.csv", mode="r", encoding="utf8") as csv_file:
    lines = {}
    for row in csv.DictReader(csv_file, skipinitialspace=True):
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
