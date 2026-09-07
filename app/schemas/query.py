"""
SatQuery AI - Query & Intent Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class QueryCreateRequest(BaseModel):
    query: str = Field(..., min_length=2, json_schema_extra={"example": "What changed between these two temporal images?"})
    image_ids: List[str] = Field(..., min_length=1, description="List of uploaded image UUIDs")
    force_task: Optional[str] = Field(None, description="Optional manual override for task routing")


class QueryIntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_text: str
    detected_intent: str
    intent_confidence: float
    task_type: str
    planner_output: Optional[Dict[str, Any]] = None
    created_at: datetime
