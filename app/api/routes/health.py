"""
SatQuery AI - Health & System Status APIs
"""
import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db
from app.agent.registry import ToolRegistry
from app.core.config import settings
from app.schemas.response import APIResponse

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("", response_model=APIResponse[Dict[str, Any]])
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """System health inspection covering database connectivity, model registry, and storage."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy ({str(e)})"

    registry = ToolRegistry.get_instance()
    storage_writable = os.access(settings.UPLOAD_DIR, os.W_OK)

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data={
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "demo_mode": settings.DEMO_MODE,
            "components": {
                "api": "healthy",
                "database": db_status,
                "tool_registry": f"healthy ({len(registry.list_tools())} tools loaded)",
                "storage": "writable" if storage_writable else "read-only",
            },
            "device": settings.MODEL_DEVICE
        },
        request_id=request_id
    )


@router.get("/ready", response_model=APIResponse[Dict[str, str]])
async def readiness_probe(request: Request):
    """Simple readiness probe for Docker / Kubernetes."""
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data={"status": "ready"},
        request_id=request_id
    )
