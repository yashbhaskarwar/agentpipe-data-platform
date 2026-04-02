import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.db import get_cursor


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Tool 1
def get_pipeline_status(pipeline_name: str, date: str | None = None) -> dict[str, Any]:
    try:
        with get_cursor() as cur:
            if date:
                cur.execute(
                    """
                    SELECT id, pipeline_name, status, start_time, end_time,
                           rows_processed, error_message
                    FROM   pipeline_runs
                    WHERE  pipeline_name = %(name)s
                      AND  DATE(start_time) = %(date)s
                    ORDER  BY start_time DESC
                    LIMIT  1
                    """,
                    {"name": pipeline_name, "date": date},
                )
            else:
                cur.execute(
                    """
                    SELECT id, pipeline_name, status, start_time, end_time,
                           rows_processed, error_message
                    FROM   pipeline_runs
                    WHERE  pipeline_name = %(name)s
                    ORDER  BY start_time DESC
                    LIMIT  1
                    """,
                    {"name": pipeline_name},
                )

            row = cur.fetchone()

        if not row:
            qualifier = f" on {date}" if date else ""
            return {
                "found": False,
                "message": f"No runs found for pipeline '{pipeline_name}'{qualifier}.",
            }

        run = dict(row)
        # Convert datetimes to ISO strings for JSON serialisation
        run["start_time"] = run["start_time"].isoformat() if run["start_time"] else None
        run["end_time"] = run["end_time"].isoformat() if run["end_time"] else None
        run["found"] = True
        return run

    except Exception as exc:
        return {"error": str(exc)}

# Tool 2
def get_failed_runs(days: int) -> dict[str, Any]:
    try:
        cutoff = _utc_now() - timedelta(days=days)

        with get_cursor() as cur:
            cur.execute(
                """
                SELECT id, pipeline_name, status, start_time, end_time,
                       rows_processed, error_message
                FROM   pipeline_runs
                WHERE  status      = 'failed'
                  AND  start_time >= %(cutoff)s
                ORDER  BY start_time DESC
                """,
                {"cutoff": cutoff},
            )
            rows = cur.fetchall()

        runs = []
        for row in rows:
            r = dict(row)
            r["start_time"] = r["start_time"].isoformat() if r["start_time"] else None
            r["end_time"] = r["end_time"].isoformat() if r["end_time"] else None
            runs.append(r)

        return {
            "days": days,
            "total_failed": len(runs),
            "runs": runs,
        }

    except Exception as exc:
        return {"error": str(exc)}