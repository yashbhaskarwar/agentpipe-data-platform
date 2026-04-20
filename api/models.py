from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

# Response envelope
class ApiResponse(BaseModel, Generic[T]):
    """Standard response wrapper for every endpoint."""
    success: bool
    data: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, message: str) -> "ApiResponse[None]":
        return cls(success=False, data=None, error=message)

# Health
class HealthData(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"

# Chat
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language message")
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for multi-turn conversations. Omit to start fresh.",
    )

class ChatData(BaseModel):
    response: str
    session_id: str

# Pipeline runs 
class PipelineRunRecord(BaseModel):
    id: int
    pipeline_name: str
    status: str
    start_time: str | None
    end_time: str | None
    rows_processed: int | None
    error_message: str | None

class PipelinesData(BaseModel):
    pipelines: list[PipelineRunRecord]
    total: int

class RunsData(BaseModel):
    runs: list[PipelineRunRecord]
    total: int
    days: int

# Quality checks 
class QualityIssueRecord(BaseModel):
    id: int
    run_id: int
    pipeline_name: str
    check_name: str
    passed: bool
    details: str | None
    checked_at: str | None

class QualityData(BaseModel):
    issues: list[QualityIssueRecord]
    total: int
    days: int

# Trigger
class TriggerData(BaseModel):
    run_id: int
    pipeline_name: str
    status: str
    start_time: str
    message: str
