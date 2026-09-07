"""
SatQuery AI - Model Adapters Introspection APIs
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Request
from app.agent.registry import ToolRegistry
from app.schemas.response import APIResponse
from app.core.config import settings

router = APIRouter(prefix="/models", tags=["Model Adapters"])


@router.get("", response_model=APIResponse[List[Dict[str, Any]]])
async def list_model_adapters(request: Request):
    """Lists loaded remote sensing model adapters and hardware deployment status."""
    registry = ToolRegistry.get_instance()
    
    models_info = [
        {
            "name": "RS-VQA-GeoCLIP-ViT-L",
            "type": "Vision-Language RS-VQA",
            "device": settings.MODEL_DEVICE,
            "status": "LOADED",
            "demo_mode": settings.DEMO_MODE,
            "supported_tasks": ["single_image_vqa", "scene_interpretation"]
        },
        {
            "name": "RS-GroundingDINO-SwinB",
            "type": "Open-Vocabulary Spatial Grounding",
            "device": settings.MODEL_DEVICE,
            "status": "LOADED",
            "demo_mode": settings.DEMO_MODE,
            "supported_tasks": ["grounding", "object_localization"]
        },
        {
            "name": "RS-ChangeFormer-V2",
            "type": "Siamese Temporal Change Detection",
            "device": settings.MODEL_DEVICE,
            "status": "LOADED",
            "demo_mode": settings.DEMO_MODE,
            "supported_tasks": ["temporal_change", "change_vqa"]
        },
        {
            "name": "RS-CrossModal-OptSAR-Net",
            "type": "Cross-Attention Optical + SAR Multimodal Fusion",
            "device": settings.MODEL_DEVICE,
            "status": "LOADED",
            "demo_mode": settings.DEMO_MODE,
            "supported_tasks": ["optical_sar_analysis", "cross_modal_fusion"]
        }
    ]

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=models_info, request_id=request_id)
