import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

APP_ENV = os.getenv("APP_ENV", "local")
ENV_FILE = f".env.{APP_ENV}"
if Path(ENV_FILE).exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


def create_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url is None:
        raise ValueError("DATABASE_URL environment variable is not set")

    return psycopg.connect(database_url, row_factory=dict_row)


def get_db():
    connection = create_connection()

    try:
        yield connection
    finally:
        connection.close()
