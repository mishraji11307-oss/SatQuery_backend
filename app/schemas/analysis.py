"""
SatQuery AI - Analysis Request, Plan, Trace & Result Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.evidence import EvidenceItemSchema


class AnalysisRequest(BaseModel):
    query: str = Field(..., min_length=2, json_schema_extra={"example": "Detect changes between T1 and T2 images and highlight new structures."})
    image_ids: List[str] = Field(..., min_length=1, description="List of uploaded image UUIDs")
    async_mode: bool = Field(default=False, description="If true, returns job_id immediately for polling")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional inference hyperparameters")


class ExecutionStepTrace(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_order: int
    step_name: str
    status: str
    summary: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0


class ExecutionPlanSchema(BaseModel):
    task: str = Field(..., json_schema_extra={"example": "temporal_change"})
    intent_confidence: float = Field(default=1.0)
    selected_tools: List[str] = Field(..., json_schema_extra={"example": ["change_detection_tool", "change_vqa_tool"]})
    input_image_ids: List[str]
    input_modalities: List[str]
    requires_registration: bool = False
    requires_optical_sar_fusion: bool = False
    validation_status: str = "VALIDATED"
    policy_checks: List[str] = Field(default_factory=list)


class ConfidenceScoreSchema(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, json_schema_extra={"example": 0.91})
    level: str = Field(..., json_schema_extra={"example": "high"})
    cross_modal_agreement: Optional[str] = Field(None, json_schema_extra={"example": "high"})
    optical_confidence: Optional[float] = None
    sar_confidence: Optional[float] = None
    factors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AnalysisResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_id: str
    job_id: str
    status: str = Field(..., json_schema_extra={"example": "SUCCESS"})
    query: str
    task: str
    answer: Optional[str] = None
    confidence: ConfidenceScoreSchema
    evidence: List[EvidenceItemSchema] = Field(default_factory=list)
    execution_plan: Optional[ExecutionPlanSchema] = None
    execution_trace: List[ExecutionStepTrace] = Field(default_factory=list)
    execution_duration_ms: float = 0.0
    created_at: datetime
