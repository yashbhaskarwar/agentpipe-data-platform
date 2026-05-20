import sys
import os
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import (
    get_pipeline_status,
    get_failed_runs,
    trigger_pipeline_run,
)

def _make_mock_cursor(fetchone_return=None, fetchall_return=None):
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.fetchall.return_value = fetchall_return or []
    return cursor


@contextmanager
def _mock_get_cursor(cursor):
    with patch("agent.tools.get_cursor") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(return_value=cursor)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_ctx

# Unit test 1: get_pipeline_status — found
def test_get_pipeline_status_returns_run_when_found():
    fake_row = {
        "id": 7,
        "pipeline_name": "ingestion",
        "status": "success",
        "start_time": datetime(2024, 1, 15, 2, 0, 0),
        "end_time": datetime(2024, 1, 15, 2, 14, 23),
        "rows_processed": 123456,
        "error_message": None,
    }
    cursor = _make_mock_cursor(fetchone_return=fake_row)

    with _mock_get_cursor(cursor):
        result = get_pipeline_status("ingestion")

    assert result["found"] is True
    assert result["id"] == 7
    assert result["pipeline_name"] == "ingestion"
    assert result["status"] == "success"
    assert result["rows_processed"] == 123456
    assert result["error_message"] is None
    # Datetimes must be serialised to ISO strings
    assert isinstance(result["start_time"], str)
    assert "2024-01-15" in result["start_time"]

# Unit test 2: get_pipeline_status — not found 
def test_get_pipeline_status_returns_not_found_when_empty():
    cursor = _make_mock_cursor(fetchone_return=None)

    with _mock_get_cursor(cursor):
        result = get_pipeline_status("transformation", date="2020-01-01")

    assert result["found"] is False
    assert "transformation" in result["message"]
    assert "2020-01-01" in result["message"]


# Unit test 3: trigger_pipeline_run — invalid name 
def test_trigger_pipeline_run_rejects_unknown_pipeline():
    with patch("agent.tools.get_cursor") as mock_ctx:
        result = trigger_pipeline_run("nonexistent_pipeline")

        # DB should NOT have been called
        mock_ctx.assert_not_called()

    assert result["triggered"] is False
    assert "error" in result
    assert "nonexistent_pipeline" in result["error"]
    assert "ingestion" in result["error"]  # valid options listed

# Unit test 4: get_failed_runs — correct structure
def test_get_failed_runs_returns_correct_structure():
    fake_rows = [
        {
            "id": 3,
            "pipeline_name": "quality_check",
            "status": "failed",
            "start_time": datetime(2024, 1, 10, 8, 0, 0),
            "end_time": datetime(2024, 1, 10, 8, 5, 0),
            "rows_processed": 0,
            "error_message": "Null rate exceeded threshold",
        },
        {
            "id": 5,
            "pipeline_name": "ingestion",
            "status": "failed",
            "start_time": datetime(2024, 1, 12, 3, 0, 0),
            "end_time": datetime(2024, 1, 12, 3, 2, 0),
            "rows_processed": 1000,
            "error_message": "Schema mismatch",
        },
    ]
    cursor = _make_mock_cursor(fetchall_return=fake_rows)

    with _mock_get_cursor(cursor):
        result = get_failed_runs(days=7)

    assert result["days"] == 7
    assert result["total_failed"] == 2
    assert len(result["runs"]) == 2
    for run in result["runs"]:
        assert isinstance(run["start_time"], str)
        assert run["status"] == "failed"

# Unit test 5: tool error handling
def test_get_pipeline_status_returns_error_dict_on_db_failure():
    with patch("agent.tools.get_cursor") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused")
        )
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = get_pipeline_status("ingestion")

    assert "error" in result
    assert "connection refused" in result["error"]
