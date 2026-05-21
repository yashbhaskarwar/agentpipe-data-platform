import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _make_app_client():
    with patch("db.async_db.init_pool", new_callable=AsyncMock), \
         patch("db.async_db.close_pool", new_callable=AsyncMock):
        from api.app import app
        return TestClient(app, raise_server_exceptions=True)

# Integration test 1: GET /health
def test_health_endpoint_returns_200_and_envelope():
    client = _make_app_client()

    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("api.app.get_pool", return_value=mock_pool):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "data" in body
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "connected"

# Integration test 2: GET /pipelines
def test_pipelines_endpoint_returns_pipeline_list():
    fake_pipelines = [
        {
            "id": 1,
            "pipeline_name": "ingestion",
            "status": "success",
            "start_time": "2024-01-15T02:00:00",
            "end_time": "2024-01-15T02:14:23",
            "rows_processed": 123456,
            "error_message": None,
        },
        {
            "id": 2,
            "pipeline_name": "transformation",
            "status": "failed",
            "start_time": "2024-01-15T03:00:00",
            "end_time": "2024-01-15T03:05:11",
            "rows_processed": 0,
            "error_message": "Schema mismatch",
        },
    ]

    client = _make_app_client()

    with patch("api.app.fetch_all_pipeline_statuses", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = fake_pipelines
        response = client.get("/pipelines")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["total"] == 2
    assert len(body["data"]["pipelines"]) == 2

    names = {p["pipeline_name"] for p in body["data"]["pipelines"]}
    assert names == {"ingestion", "transformation"}

# Integration test 3: POST /trigger/{pipeline_name} — invalid name 
def test_trigger_endpoint_rejects_unknown_pipeline():
    client = _make_app_client()

    with patch("api.app.insert_pipeline_run", new_callable=AsyncMock) as mock_insert:
        response = client.post("/trigger/does_not_exist")
        mock_insert.assert_not_called()

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] is not None
    assert "does_not_exist" in body["error"]

# Integration test 4: POST /trigger/{pipeline_name} — valid name
def test_trigger_endpoint_creates_run_and_returns_run_id():
    fake_record = {
        "id": 99,
        "pipeline_name": "ingestion",
        "status": "running",
        "start_time": "2024-01-15T10:00:00",
    }

    client = _make_app_client()

    with patch("api.app.insert_pipeline_run", new_callable=AsyncMock) as mock_insert:
        mock_insert.return_value = fake_record
        response = client.post("/trigger/ingestion")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["run_id"] == 99
    assert body["data"]["status"] == "running"
    assert body["data"]["pipeline_name"] == "ingestion"
    assert "99" in body["data"]["message"]

# Integration test 5: GET /runs — query parameter validation 
def test_runs_endpoint_rejects_out_of_range_days():
    client = _make_app_client()
    response = client.get("/runs?days=0")
    assert response.status_code == 422
    