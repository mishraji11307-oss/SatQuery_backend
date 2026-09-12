"""
SatQuery AI - Sample Data & AI Data Catalog Routes
"""
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from app.core.config import settings
from app.schemas.response import APIResponse

router = APIRouter(prefix="/data", tags=["Data Catalog"])


@router.get("/samples", response_model=APIResponse[List[Dict[str, Any]]])
async def list_sample_data(request: Request):
    """Return a discoverable list of bundled AI demo satellite sample files.

    This gives the frontend and any downstream agent a stable contract for
    loading the repository's demo optical, SAR, and temporal data.
    """
    sample_dir = os.path.join(settings.BASE_DIR, "sample_data")
    sample_files = []

    if os.path.isdir(sample_dir):
        for filename in sorted(os.listdir(sample_dir)):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
                continue

            lower = filename.lower()
            if lower.startswith("optical"):
                modality = "optical"
                task = "single_image_vqa"
            elif lower.startswith("sar"):
                modality = "sar"
                task = "optical_sar_analysis"
            elif lower.startswith("t1"):
                modality = "optical"
                task = "temporal_change"
            elif lower.startswith("t2"):
                modality = "optical"
                task = "temporal_change"
            else:
                modality = "optical"
                task = "single_image_vqa"

            filepath = os.path.join(sample_dir, filename)
            sample_files.append({
                "name": filename,
                "modality": modality,
                "task": task,
                "size_bytes": os.path.getsize(filepath),
                "preview_url": f"/sample_data/{filename}",
                "description": f"Bundled {modality.upper()} remote sensing demo sample for SatQuery AI",
            })

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=sample_files, request_id=request_id)
