"""
SatQuery AI - Standardized API Response Envelopes
"""
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIError(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context or validation details")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = Field(..., description="Indicates if the request succeeded")
    data: Optional[DataT] = Field(default=None, description="Payload data returned by endpoint")
    error: Optional[APIError] = Field(default=None, description="Error object if success is false")
    request_id: str = Field(default="unknown", description="Unique request tracing ID")
