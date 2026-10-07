import os

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_DSN = psycopg2.extensions.make_dsn(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)


def get_db_connection() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(DATABASE_DSN, cursor_factory=RealDictCursor)
    return conn
