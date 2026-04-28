import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.logger import get_logger, log_request
from api.models import (
    ApiResponse,
    ChatData,
    ChatRequest,
    HealthData,
    PipelineRunRecord,
    PipelinesData,
    QualityData,
    QualityIssueRecord,
    RunsData,
    TriggerData,
)
from backend.db.async_db import (
    close_pool,
    fetch_all_pipeline_statuses,
    fetch_quality_issues,
    fetch_recent_runs,
    get_pool,
    init_pool,
    insert_pipeline_run,
)

logger = get_logger("agentpipe.api")

_sessions: dict[str, list[dict[str, Any]]] = {}

VALID_PIPELINES = {"ingestion", "transformation", "quality_check"}

limiter = Limiter(key_func=get_remote_address, default_limits=[])

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting AgentPipe API", extra={"event": "startup"})
    await init_pool()
    logger.info("Database pool initialised", extra={"event": "startup"})

    yield

    logger.info("Shutting down AgentPipe API", extra={"event": "shutdown"})
    await close_pool()

app = FastAPI(
    title="AgentPipe",
    description="Conversational Data Pipeline Agent — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> Response:
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    log_request(
        logger=logger,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_ip=get_remote_address(request),
    )

    return response

def _error_response(message: str, status_code: int = 500) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse.fail(message).model_dump(),
    )

@app.get(
    "/health",
    response_model=ApiResponse[HealthData],
    summary="Health check",
    tags=["meta"],
)
async def health() -> ApiResponse[HealthData]:
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as exc:
        logger.error("Database health check failed", extra={"error": str(exc)})
        db_status = "unavailable"

    return ApiResponse.ok(
        HealthData(status="ok", database=db_status)
    )

@app.post(
    "/chat",
    response_model=ApiResponse[ChatData],
    summary="Natural language agent interface",
    tags=["agent"],
)
@limiter.limit("10/minute")
async def chat(request: Request, body: ChatRequest) -> ApiResponse[ChatData]:
    session_id = body.session_id or str(uuid.uuid4())
    history = _sessions.get(session_id, [])

    t0 = time.perf_counter()

    try:
        from agent.agent import run_agent

        response_text, updated_history = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: run_agent(body.message, history),
        )
    except Exception as exc:
        logger.error(
            "Agent error",
            extra={
                "event": "agent_error",
                "session_id": session_id,
                "error": str(exc),
            },
        )

        return JSONResponse(
            status_code=500,
            content=ApiResponse.fail(f"Agent error: {exc}").model_dump(),
        )

    _sessions[session_id] = updated_history

    duration_ms = (time.perf_counter() - t0) * 1000

    logger.info(
        "Chat request completed",
        extra={
            "event": "chat_complete",
            "session_id": session_id,
            "duration_ms": round(duration_ms, 2),
            "history_turns": len(updated_history),
        },
    )

    return ApiResponse.ok(
        ChatData(response=response_text, session_id=session_id)
    )

@app.get(
    "/pipelines",
    response_model=ApiResponse[PipelinesData],
    summary="Latest status for all pipelines",
    tags=["pipelines"],
)
async def get_pipelines() -> ApiResponse[PipelinesData]:
    try:
        rows = await fetch_all_pipeline_statuses()
    except Exception as exc:
        logger.error("Failed to fetch pipeline statuses", extra={"error": str(exc)})
        return _error_response("Failed to fetch pipeline statuses.")

    pipelines = [PipelineRunRecord(**row) for row in rows]

    return ApiResponse.ok(
        PipelinesData(pipelines=pipelines, total=len(pipelines))
    )

@app.get(
    "/runs",
    response_model=ApiResponse[RunsData],
    summary="Recent pipeline runs",
    tags=["pipelines"],
)
async def get_runs(
    days: int = Query(default=7, ge=1, le=90, description="Look-back window in days"),
) -> ApiResponse[RunsData]:
    try:
        rows = await fetch_recent_runs(days)
    except Exception as exc:
        logger.error("Failed to fetch runs", extra={"error": str(exc), "days": days})
        return _error_response("Failed to fetch pipeline runs.")

    runs = [PipelineRunRecord(**row) for row in rows]

    return ApiResponse.ok(
        RunsData(runs=runs, total=len(runs), days=days)
    )

@app.get(
    "/quality",
    response_model=ApiResponse[QualityData],
    summary="Recent data quality issues",
    tags=["quality"],
)
async def get_quality(
    days: int = Query(default=7, ge=1, le=90, description="Look-back window in days"),
) -> ApiResponse[QualityData]:
    try:
        rows = await fetch_quality_issues(days)
    except Exception as exc:
        logger.error(
            "Failed to fetch quality issues",
            extra={"error": str(exc), "days": days},
        )
        return _error_response("Failed to fetch quality issues.")

    issues = [QualityIssueRecord(**row) for row in rows]

    return ApiResponse.ok(
        QualityData(issues=issues, total=len(issues), days=days)
    )

@app.post(
    "/trigger/{pipeline_name}",
    response_model=ApiResponse[TriggerData],
    summary="Trigger a pipeline run",
    tags=["pipelines"],
)
async def trigger_pipeline(pipeline_name: str) -> ApiResponse[TriggerData]:
    if pipeline_name not in VALID_PIPELINES:
        return JSONResponse(
            status_code=422,
            content=ApiResponse.fail(
                f"Unknown pipeline '{pipeline_name}'. "
                f"Valid options: {', '.join(sorted(VALID_PIPELINES))}"
            ).model_dump(),
        )

    try:
        record = await insert_pipeline_run(pipeline_name)
    except Exception as exc:
        logger.error(
            "Failed to trigger pipeline",
            extra={"pipeline": pipeline_name, "error": str(exc)},
        )
        return _error_response("Failed to trigger pipeline run.")

    logger.info(
        "Pipeline triggered",
        extra={
            "event": "pipeline_triggered",
            "pipeline_name": pipeline_name,
            "run_id": record["id"],
        },
    )

    return ApiResponse.ok(
        TriggerData(
            run_id=record["id"],
            pipeline_name=record["pipeline_name"],
            status=record["status"],
            start_time=record["start_time"],
            message=f"Pipeline '{pipeline_name}' triggered. Run ID: {record['id']}.",
        )
    )