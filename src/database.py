import array
import csv
import time

import sqlalchemy

from src.datatypes import Character, Movie, Conversation, Line
import os
import io
from supabase import Client, create_client
import dotenv

# DO NOT CHANGE THIS TO BE HARDCODED. ONLY PULL FROM ENVIRONMENT VARIABLES.
dotenv.load_dotenv()
DB_USER: str = os.environ.get("POSTGRES_USER")
DB_PASSWD = os.environ.get("POSTGRES_PASSWORD")
DB_SERVER: str = os.environ.get("POSTGRES_SERVER")
DB_PORT: str = os.environ.get("POSTGRES_PORT")
DB_NAME: str = os.environ.get("POSTGRES_DB")

# Create a new DB engine based on our connection string
engine = sqlalchemy.create_engine(f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}")

# Create a single connection to the database. Later we will discuss pooling connections.
conn = engine.connect()

metadata_obj = sqlalchemy.MetaData()
movies = sqlalchemy.Table("movies", metadata_obj, autoload_with=engine)
characters = sqlalchemy.Table("characters", metadata_obj, autoload_with=engine)
conversations = sqlalchemy.Table("conversations", metadata_obj, autoload_with=engine)
lines = sqlalchemy.Table("lines", metadata_obj, autoload_with=engine)

