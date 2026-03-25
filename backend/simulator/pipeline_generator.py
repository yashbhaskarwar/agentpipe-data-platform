import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import get_cursor, apply_schema

PIPELINES = ["ingestion", "transformation", "quality_check"]

TASKS: dict[str, list[str]] = {
    "ingestion": [
        "extract_source_data",
        "validate_schema",
        "load_to_staging",
        "update_watermark",
    ],
    "transformation": [
        "read_staging",
        "apply_business_rules",
        "deduplicate_records",
        "write_to_warehouse",
    ],
    "quality_check": [
        "run_null_checks",
        "run_range_checks",
        "run_referential_checks",
        "publish_dq_report",
    ],
}

QUALITY_CHECKS: dict[str, list[str]] = {
    "ingestion": [
        "row_count_nonzero",
        "no_duplicate_primary_keys",
        "timestamp_not_null",
    ],
    "transformation": [
        "revenue_column_positive",
        "customer_id_valid_format",
        "no_orphan_records",
    ],
    "quality_check": [
        "null_rate_below_threshold",
        "outlier_score_within_bounds",
        "referential_integrity_ok",
    ],
}

PIPELINE_ROW_RANGES: dict[str, tuple[int, int]] = {
    "ingestion":       (50_000, 500_000),
    "transformation":  (45_000, 490_000),
    "quality_check":   (45_000, 490_000),
}

PIPELINE_DURATION_RANGES: dict[str, tuple[int, int]] = {  # seconds
    "ingestion":      (180, 900),
    "transformation": (120, 600),
    "quality_check":  (60,  300),
}

FAILURE_MESSAGES: list[str] = [
    "Connection timeout to source system after 30s",
    "Schema mismatch: expected column 'event_ts' not found",
    "Duplicate key violation on table staging.events",
    "Memory limit exceeded during sort operation",
    "S3 throttling error: SlowDown — retry limit reached",
    "Referential integrity check failed: 1,203 orphan records detected",
    "Null rate 18.4% exceeds threshold of 5% for column 'customer_id'",
    "Source API returned HTTP 503 — service unavailable",
]

DAYS_BACK = 30
RUNS_PER_DAY_RANGE = (1, 2)   

# For historical runs 
HISTORICAL_WEIGHTS = ["success"] * 88 + ["failed"] * 12

LATEST_WEIGHTS = ["success"] * 79 + ["failed"] * 13 + ["running"] * 8

def _random_start(base_date: datetime) -> datetime:
    """Return a random start time within the given UTC day."""
    offset_minutes = random.randint(0, 23 * 60 + 59)
    return base_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        minutes=offset_minutes
    )

def _task_status(run_status: str, task_index: int, total_tasks: int) -> str:
    """
    Derive individual task status from the overall run status.
    """
    if run_status in ("success", "running"):
        return "success"
    # failed: pick a failure point (at least 1 task succeeded before failure)
    failure_point = random.randint(0, total_tasks - 1)
    if task_index < failure_point:
        return "success"
    if task_index == failure_point:
        return "failed"
    return "skipped"

def _insert_run(
    cur,
    pipeline_name: str,
    status: str,
    start_time: datetime,
) -> int:
    """Insert a pipeline_runs record and return its generated id."""
    duration = random.randint(*PIPELINE_DURATION_RANGES[pipeline_name])

    if status == "running":
        end_time = None
        rows_processed = None
        error_message = None
    elif status == "success":
        end_time = start_time + timedelta(seconds=duration)
        rows_processed = random.randint(*PIPELINE_ROW_RANGES[pipeline_name])
        error_message = None
    else:  # failed
        # Fails somewhere between 20%–80% of expected duration
        failure_offset = int(duration * random.uniform(0.2, 0.8))
        end_time = start_time + timedelta(seconds=failure_offset)
        rows_processed = random.randint(
            0, PIPELINE_ROW_RANGES[pipeline_name][0] // 2
        )
        error_message = random.choice(FAILURE_MESSAGES)

    cur.execute(
        """
        INSERT INTO pipeline_runs
               (pipeline_name, status, start_time, end_time, rows_processed, error_message)
        VALUES (%(pipeline_name)s, %(status)s, %(start_time)s,
                %(end_time)s, %(rows_processed)s, %(error_message)s)
        RETURNING id
        """,
        {
            "pipeline_name": pipeline_name,
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "rows_processed": rows_processed,
            "error_message": error_message,
        },
    )
    return cur.fetchone()["id"]
