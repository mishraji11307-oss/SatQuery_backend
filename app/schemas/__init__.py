"""
SatQuery AI - Schemas Package
"""
from app.schemas.response import APIResponse, APIError
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    AuthMeResponse,
)
from app.schemas.upload import ImageMetadataSchema, UploadResponse, UploadListResponse
from app.schemas.query import QueryCreateRequest, QueryIntentResponse
from app.schemas.evidence import EvidenceItemSchema, BoundingBox, GeoPolygon
from app.schemas.analysis import (
    AnalysisRequest,
    ExecutionStepTrace,
    ExecutionPlanSchema,
    ConfidenceScoreSchema,
    AnalysisResultSchema,
)
from app.schemas.job import JobStatusResponse, JobDetailResponse

__all__ = [
    "APIResponse",
    "APIError",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserResponse",
    "AuthMeResponse",
    "ImageMetadataSchema",
    "UploadResponse",
    "UploadListResponse",
    "QueryCreateRequest",
    "QueryIntentResponse",
    "EvidenceItemSchema",
    "BoundingBox",
    "GeoPolygon",
    "AnalysisRequest",
    "ExecutionStepTrace",
    "ExecutionPlanSchema",
    "ConfidenceScoreSchema",
    "AnalysisResultSchema",
    "JobStatusResponse",
    "JobDetailResponse",
]
