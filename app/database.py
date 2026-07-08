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


def get_db():
    database_url = os.getenv("DATABASE_URL")

    connection = psycopg.connect(database_url, row_factory=dict_row)

    try:
        yield connection
    finally:
        connection.close()
