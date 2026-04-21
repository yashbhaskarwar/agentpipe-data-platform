import os
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Module-level pool
_pool: asyncpg.Pool | None = None

async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        min_size=2,
        max_size=10,
        command_timeout=30,
    )

async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Call init_pool() first.")
    return _pool
