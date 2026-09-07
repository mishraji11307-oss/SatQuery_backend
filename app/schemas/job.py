"""
SatQuery AI - Background Job Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.analysis import AnalysisResultSchema


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str = Field(..., json_schema_extra={"example": "PROCESSING"})
    progress: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class JobDetailResponse(JobStatusResponse):
    result: Optional[AnalysisResultSchema] = None
