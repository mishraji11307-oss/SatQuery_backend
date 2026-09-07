"""
SatQuery AI - Upload & Geospatial Metadata Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ImageMetadataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    width: int
    height: int
    num_bands: int
    dtype: str
    crs: Optional[str] = None
    transform: Optional[List[float]] = None
    bounds: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    resolution_x: Optional[float] = None
    resolution_y: Optional[float] = None
    acquisition_date: Optional[datetime] = None
    sensor: Optional[str] = None
    is_georeferenced: bool = False
    extra_metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    file_format: str
    modality: str
    tag: Optional[str] = None
    created_at: datetime
    metadata: Optional[ImageMetadataSchema] = None
    preview_url: Optional[str] = None


class UploadListResponse(BaseModel):
    total: int
    images: List[UploadResponse]
