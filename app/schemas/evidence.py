"""
SatQuery AI - Evidence Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BoundingBox(BaseModel):
    label: str = Field(..., json_schema_extra={"example": "aircraft"})
    confidence: float = Field(..., ge=0.0, le=1.0)
    box_2d: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] normalized coordinates")
    geo_bbox: Optional[List[float]] = None


class GeoPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class EvidenceItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    evidence_type: str = Field(..., description="e.g. bounding_box, change_mask, optical_evidence, sar_evidence, comparison")
    url: Optional[str] = Field(None, description="Direct URL to generated evidence image artifact")
    file_path: Optional[str] = None
    bbox: Optional[List[float]] = None
    bboxes: Optional[List[BoundingBox]] = None
    geo_polygon: Optional[Dict[str, Any]] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_tool: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
