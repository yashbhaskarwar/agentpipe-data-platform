from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models import (
    ApiResponse,
    HealthData,
    PipelineRunRecord,
    PipelinesData,
    QualityData,
    QualityIssueRecord,
    RunsData,
)
from backend.db.async_db import (
    close_pool,
    fetch_all_pipeline_statuses,
    fetch_quality_issues,
    fetch_recent_runs,
    get_pool,
    init_pool,
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_pool()
    yield
    await close_pool()

app = FastAPI(
    title="AgentPipe",
    description="Conversational Data Pipeline Agent — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def _error_response(message: str, status_code: int = 500) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse.fail(message).model_dump(),
    )

@app.get("/health", response_model=ApiResponse[HealthData], tags=["meta"])
async def health() -> ApiResponse[HealthData]:
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    return ApiResponse.ok(
        HealthData(status="ok", database=db_status)
    )

@app.get("/pipelines", response_model=ApiResponse[PipelinesData], tags=["pipelines"])
async def get_pipelines() -> ApiResponse[PipelinesData]:
    try:
        rows = await fetch_all_pipeline_statuses()
    except Exception:
        return _error_response("Failed to fetch pipeline statuses.")

    pipelines = [PipelineRunRecord(**row) for row in rows]

    return ApiResponse.ok(
        PipelinesData(pipelines=pipelines, total=len(pipelines))
    )

@app.get("/runs", response_model=ApiResponse[RunsData], tags=["pipelines"])
async def get_runs(
    days: int = Query(default=7, ge=1, le=90),
) -> ApiResponse[RunsData]:
    try:
        rows = await fetch_recent_runs(days)
    except Exception:
        return _error_response("Failed to fetch pipeline runs.")

    runs = [PipelineRunRecord(**row) for row in rows]

    return ApiResponse.ok(
        RunsData(runs=runs, total=len(runs), days=days)
    )

@app.get("/quality", response_model=ApiResponse[QualityData], tags=["quality"])
async def get_quality(
    days: int = Query(default=7, ge=1, le=90),
) -> ApiResponse[QualityData]:
    try:
        rows = await fetch_quality_issues(days)
    except Exception:
        return _error_response("Failed to fetch quality issues.")

    issues = [QualityIssueRecord(**row) for row in rows]

    return ApiResponse.ok(
        QualityData(issues=issues, total=len(issues), days=days)
    )
