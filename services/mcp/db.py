"""
Database connection pool - async (asyncpg)
================================================
init_pool()  - called once at app startup; retries until DB is up.
get_pool()   - returns the live pool (use inside route handlers).
close_pool() - called at shutdown.
"""

import os
import asyncio
import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool(retries: int = 15, delay: float = 3.0):
    """
    Create the connection pool. Retries so the MCP server can start
    before TimescaleDB is fully ready.
    """
    global _pool

    for attempt in range(1, retries + 1):
        try:
            _pool = await asyncpg.create_pool(
                host     = os.getenv("DB_HOST",     "localhost"),
                port     = int(os.getenv("DB_PORT", "5432")),
                user     = os.getenv("DB_USER",     "postgres"),
                password = os.getenv("DB_PASSWORD", "postgres"),
                database = os.getenv("DB_NAME",     "maritime_telemetry"),
                min_size = 2,
                max_size = 10,
            )
            print(f"[mcp] DB pool ready (attempt {attempt})")
            return
        except Exception as exc:  # pragma: no cover
            print(f"[mcp] DB not ready - attempt {attempt}/{retries}: {exc}")
            await asyncio.sleep(delay)

    raise RuntimeError("Could not connect to the database after retries.")


def get_pool() -> asyncpg.Pool:
    """Return the active pool. Raises if init_pool() was not called."""
    if _pool is None:
        raise RuntimeError("DB pool not initialised - call init_pool() first.")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
