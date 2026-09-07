"""
SatQuery AI - SQLAlchemy ORM Models
Defines relational schema for Earth Observation multimodal assistant.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    uploads = relationship("UploadedImage", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    queries = relationship("QueryRecord", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    jobs = relationship("AnalysisJob", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_format = Column(String(50), nullable=False)
    modality = Column(String(50), default="optical", index=True)  # optical, sar, multispectral, unknown
    tag = Column(String(50), nullable=True)  # t1, t2, optical, sar, reference
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="uploads", lazy="selectin")
    image_metadata = relationship("ImageMetadata", back_populates="image", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("uploaded_images.id", ondelete="CASCADE"), unique=True, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    num_bands = Column(Integer, nullable=False)
    dtype = Column(String(50), nullable=False)
    crs = Column(String(100), nullable=True)
    transform = Column(JSON, nullable=True)
    bounds = Column(JSON, nullable=True)  # [minx, miny, maxx, maxy]
    resolution_x = Column(Float, nullable=True)
    resolution_y = Column(Float, nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    sensor = Column(String(100), nullable=True)
    is_georeferenced = Column(Boolean, default=False)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    image = relationship("UploadedImage", back_populates="image_metadata", lazy="selectin")


class QueryRecord(Base):
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    detected_intent = Column(String(100), nullable=False)
    intent_confidence = Column(Float, default=1.0)
    task_type = Column(String(100), nullable=False)
    planner_output = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="queries", lazy="selectin")
    jobs = relationship("AnalysisJob", back_populates="query", lazy="selectin")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    query_id = Column(String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=True, index=True)
    image_ids = Column(JSON, nullable=False, default=list)  # List[str] of uploaded image IDs
    status = Column(String(50), default="QUEUED", index=True)  # QUEUED, VALIDATING, PROCESSING, COMPLETED, FAILED, CANCELLED
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="jobs", lazy="selectin")
    query = relationship("QueryRecord", back_populates="jobs", lazy="selectin")
    result = relationship("AnalysisResult", back_populates="job", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    tool_executions = relationship("ToolExecution", back_populates="job", cascade="all, delete-orphan", lazy="selectin")
    traces = relationship("ExecutionTrace", back_populates="job", cascade="all, delete-orphan", lazy="selectin")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(50), default="1.0.0")
    model_name = Column(String(100), nullable=True)
    status = Column(String(50), default="SUCCESS")
    duration_ms = Column(Float, default=0.0)
    input_parameters = Column(JSON, nullable=True)
    output_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("AnalysisJob", back_populates="tool_executions", lazy="selectin")
    evidence = relationship("EvidenceItem", back_populates="tool_execution", lazy="selectin")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    answer = Column(Text, nullable=True)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, INSUFFICIENT_EVIDENCE, ERROR
    overall_confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)  # high, medium, low
    cross_modal_agreement = Column(String(50), nullable=True)  # high, partial, low, na
    confidence_factors = Column(JSON, nullable=True)  # List[str]
    warnings = Column(JSON, nullable=True)  # List[str]
    execution_duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("AnalysisJob", back_populates="result", lazy="selectin")
    evidence_items = relationship("EvidenceItem", back_populates="result", cascade="all, delete-orphan", lazy="selectin")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    result_id = Column(String(36), ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_execution_id = Column(String(36), ForeignKey("tool_executions.id", ondelete="SET NULL"), nullable=True)
    evidence_type = Column(String(50), nullable=False)  # change_mask, bounding_box, optical_evidence, sar_evidence, comparison, polygon
    file_path = Column(String(512), nullable=True)
    url = Column(String(512), nullable=True)
    bbox = Column(JSON, nullable=True)  # [ymin, xmin, ymax, xmax] or [x, y, w, h]
    geo_polygon = Column(JSON, nullable=True)
    confidence = Column(Float, default=1.0)
    description = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    result = relationship("AnalysisResult", back_populates="evidence_items", lazy="selectin")
    tool_execution = relationship("ToolExecution", back_populates="evidence", lazy="selectin")


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False, default=0)
    step_name = Column(String(100), nullable=False)  # e.g., "QUERY_UNDERSTANDING", "INPUT_VALIDATION", "TOOL_SELECTION"
    status = Column(String(50), default="COMPLETED")  # STARTED, COMPLETED, FAILED, SKIPPED
    summary = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("AnalysisJob", back_populates="traces", lazy="selectin")
