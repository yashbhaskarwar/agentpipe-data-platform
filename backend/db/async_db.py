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

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _row_to_dict(record: asyncpg.Record) -> dict[str, Any]:
    result = {}
    for key, value in record.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

# Query functions 
async def fetch_all_pipeline_statuses() -> list[dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (pipeline_name)
                   id, pipeline_name, status, start_time, end_time,
                   rows_processed, error_message
            FROM   pipeline_runs
            ORDER  BY pipeline_name, start_time DESC
            """
        )
    return [_row_to_dict(r) for r in rows]

async def fetch_recent_runs(days: int) -> list[dict[str, Any]]:
    cutoff = _utc_now() - timedelta(days=days)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, pipeline_name, status, start_time, end_time,
                   rows_processed, error_message
            FROM   pipeline_runs
            WHERE  start_time >= $1
            ORDER  BY start_time DESC
            """,
            cutoff,
        )
    return [_row_to_dict(r) for r in rows]

async def fetch_quality_issues(days: int) -> list[dict[str, Any]]:
    cutoff = _utc_now() - timedelta(days=days)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT dq.id,
                   dq.run_id,
                   pr.pipeline_name,
                   dq.check_name,
                   dq.passed,
                   dq.details,
                   dq.checked_at
            FROM   data_quality_checks dq
            JOIN   pipeline_runs pr ON pr.id = dq.run_id
            WHERE  dq.passed      = false
              AND  dq.checked_at >= $1
            ORDER  BY dq.checked_at DESC
            """,
            cutoff,
        )
    return [_row_to_dict(r) for r in rows]