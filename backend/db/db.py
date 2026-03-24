import os
import contextlib
from typing import Generator

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def _build_dsn() -> str:
    return (
        f"host={os.environ['DB_HOST']} "
        f"port={os.environ['DB_PORT']} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )

def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(_build_dsn(), cursor_factory=psycopg2.extras.RealDictCursor)

@contextlib.contextmanager
def get_cursor() -> Generator[psycopg2.extras.RealDictCursor, None, None]:
    conn = get_connection()
    try:
        with conn:                  # auto-commit / rollback
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()

def apply_schema(schema_path: str = "db/schema.sql") -> None:
    with open(schema_path, "r") as fh:
        sql = fh.read()

    with get_cursor() as cur:
        cur.execute(sql)

    print("Schema applied successfully.")

if __name__ == "__main__":
    apply_schema()
    print("Database connection verified.")