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

 # Tool 3   
def get_data_quality_issues(days: int) -> dict[str, Any]:
    try:
        cutoff = _utc_now() - timedelta(days=days)

        with get_cursor() as cur:
            cur.execute(
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
                  AND  dq.checked_at >= %(cutoff)s
                ORDER  BY dq.checked_at DESC
                """,
                {"cutoff": cutoff},
            )
            rows = cur.fetchall()

        issues = []
        for row in rows:
            r = dict(row)
            r["checked_at"] = r["checked_at"].isoformat() if r["checked_at"] else None
            issues.append(r)

        return {
            "days": days,
            "total_issues": len(issues),
            "issues": issues,
        }

    except Exception as exc:
        return {"error": str(exc)}

# Tool 4
def trigger_pipeline_run(pipeline_name: str) -> dict[str, Any]:
    valid_pipelines = {"ingestion", "transformation", "quality_check"}
    if pipeline_name not in valid_pipelines:
        return {
            "triggered": False,
            "error": (
                f"Unknown pipeline '{pipeline_name}'. "
                f"Valid options: {', '.join(sorted(valid_pipelines))}"
            ),
        }

    try:
        start_time = _utc_now()

        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_runs
                       (pipeline_name, status, start_time)
                VALUES (%(name)s, 'running', %(start_time)s)
                RETURNING id
                """,
                {"name": pipeline_name, "start_time": start_time},
            )
            run_id = cur.fetchone()["id"]

        return {
            "triggered": True,
            "pipeline_name": pipeline_name,
            "run_id": run_id,
            "status": "running",
            "start_time": start_time.isoformat(),
            "message": (
                f"Pipeline '{pipeline_name}' triggered successfully. "
                f"Run ID: {run_id}. Status: running."
            ),
        }
    except Exception as exc:
        return {"triggered": False, "error": str(exc)}

# Tool 5
def get_run_summary(run_id: int) -> dict[str, Any]:
    try:
        with get_cursor() as cur:
            # Main run record
            cur.execute(
                """
                SELECT id, pipeline_name, status, start_time, end_time,
                       rows_processed, error_message
                FROM   pipeline_runs
                WHERE  id = %(run_id)s
                """,
                {"run_id": run_id},
            )
            run_row = cur.fetchone()

            if not run_row:
                return {"found": False, "message": f"No run found with ID {run_id}."}

            run = dict(run_row)
            run["start_time"] = run["start_time"].isoformat() if run["start_time"] else None
            run["end_time"] = run["end_time"].isoformat() if run["end_time"] else None

            # Tasks
            cur.execute(
                """
                SELECT id, task_name, status, duration_seconds, error_message
                FROM   pipeline_tasks
                WHERE  run_id = %(run_id)s
                ORDER  BY id
                """,
                {"run_id": run_id},
            )
            tasks = [dict(r) for r in cur.fetchall()]

            # Quality checks
            cur.execute(
                """
                SELECT id, check_name, passed, details, checked_at
                FROM   data_quality_checks
                WHERE  run_id = %(run_id)s
                ORDER  BY id
                """,
                {"run_id": run_id},
            )
            quality_rows = cur.fetchall()

        checks = []
        for row in quality_rows:
            r = dict(row)
            r["checked_at"] = r["checked_at"].isoformat() if r["checked_at"] else None
            checks.append(r)

        return {
            "found": True,
            "run": run,
            "tasks": tasks,
            "data_quality_checks": checks,
            "task_count": len(tasks),
            "check_count": len(checks),
            "failed_tasks": [t for t in tasks if t["status"] == "failed"],
            "failed_checks": [c for c in checks if not c["passed"]],
        }

    except Exception as exc:
        return {"error": str(exc)}

# Maps tool name strings 
TOOL_DISPATCH: dict[str, Any] = {
    "get_pipeline_status":    get_pipeline_status,
    "get_failed_runs":        get_failed_runs,
    "get_data_quality_issues": get_data_quality_issues,
    "trigger_pipeline_run":   trigger_pipeline_run,
    "get_run_summary":        get_run_summary,
}
