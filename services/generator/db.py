"""
Database connection – synchronous (psycopg2)
=============================================
get_connection() blocks and retries until TimescaleDB is ready.
Used by the generator's main loop.
"""

import os
import time
import psycopg2


def get_connection(max_retries: int = 15, retry_delay: float = 3.0):
    """
    Connect to PostgreSQL.  Retries so the generator can start
    before TimescaleDB is fully initialised.
    """
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host     = os.getenv("DB_HOST",     "localhost"),
                port     = int(os.getenv("DB_PORT", "5432")),
                user     = os.getenv("DB_USER",     "postgres"),
                password = os.getenv("DB_PASSWORD", "postgres"),
                dbname   = os.getenv("DB_NAME",     "maritime_telemetry"),
            )
            conn.autocommit = False
            print(f"[generator] Connected to database (attempt {attempt})")
            return conn
        except psycopg2.OperationalError as exc:
            print(f"[generator] DB not ready – attempt {attempt}/{max_retries}: {exc}")
            time.sleep(retry_delay)

    raise ConnectionError("Could not connect to the database after retries.")
