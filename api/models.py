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
    