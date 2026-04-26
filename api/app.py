from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import ApiResponse, HealthData
from backend.db.async_db import close_pool, get_pool, init_pool

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