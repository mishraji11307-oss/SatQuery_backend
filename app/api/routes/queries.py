"""
SatQuery AI - Query & Planning APIs
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.upload_repo import UploadRepository
from app.db.repositories.query_repo import QueryRepository
from app.db.models import User
from app.agent.planner import QueryPlanner
from app.schemas.response import APIResponse
from app.schemas.query import QueryCreateRequest, QueryIntentResponse
from app.api.dependencies import get_optional_user
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/queries", tags=["Queries & Planning"])


@router.post("", response_model=APIResponse[QueryIntentResponse], status_code=status.HTTP_200_OK)
async def analyze_query_intent(
    req: QueryCreateRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Parses natural language query, validates image inputs, and generates an execution plan.
    """
    upload_repo = UploadRepository(db)
    images = await upload_repo.get_many_by_ids(req.image_ids)
    if len(images) != len(req.image_ids):
        missing = set(req.image_ids) - {img.id for img in images}
        raise EntityNotFoundError("UploadedImage", f"Missing IDs: {missing}")

    images_meta = [
        {
            "id": img.id,
            "modality": img.modality,
            "crs": img.image_metadata.crs if img.image_metadata else None,
            "bounds": img.image_metadata.bounds if img.image_metadata else None,
        }
        for img in images
    ]

    planner = QueryPlanner()
    plan = planner.create_plan(
        query=req.query,
        uploaded_images=images_meta,
        force_task=req.force_task
    )

    query_repo = QueryRepository(db)
    user_id = current_user.id if current_user else None
    query_rec = await query_repo.create(
        query_text=req.query,
        detected_intent=plan.task,
        task_type=plan.task,
        intent_confidence=plan.intent_confidence,
        user_id=user_id,
        planner_output=plan.model_dump()
    )

    res = QueryIntentResponse(
        id=query_rec.id,
        query_text=query_rec.query_text,
        detected_intent=query_rec.detected_intent,
        intent_confidence=query_rec.intent_confidence,
        task_type=query_rec.task_type,
        planner_output=query_rec.planner_output,
        created_at=query_rec.created_at
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=res, request_id=request_id)


@router.get("/{query_id}", response_model=APIResponse[QueryIntentResponse])
async def get_query(
    query_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a previously analyzed query record."""
    query_repo = QueryRepository(db)
    query_rec = await query_repo.get_by_id(query_id)
    if not query_rec:
        raise EntityNotFoundError("QueryRecord", query_id)

    res = QueryIntentResponse.model_validate(query_rec)
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=res, request_id=request_id)
