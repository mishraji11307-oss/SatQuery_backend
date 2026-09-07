"""
SatQuery AI - Background Jobs & Status Polling APIs
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.analysis_repo import AnalysisRepository
from app.db.models import User
from app.schemas.response import APIResponse
from app.schemas.analysis import AnalysisRequest, AnalysisResultSchema, ConfidenceScoreSchema, ExecutionPlanSchema, ExecutionStepTrace
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.job import JobStatusResponse, JobDetailResponse
from app.api.dependencies import get_optional_user
from app.workers.analysis_tasks import run_async_analysis_task
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/jobs", tags=["Jobs & Polling"])


@router.post("", response_model=APIResponse[JobStatusResponse], status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_job(
    req: AnalysisRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits an asynchronous job and returns immediately with a tracking job ID."""
    analysis_repo = AnalysisRepository(db)
    user_id = current_user.id if current_user else None
    
    job = await analysis_repo.create_job(
        image_ids=req.image_ids,
        user_id=user_id,
        status="QUEUED"
    )

    background_tasks.add_task(
        run_async_analysis_task,
        query_text=req.query,
        image_ids=req.image_ids,
        user_id=user_id,
        job_id=job.id,
        parameters=req.parameters
    )

    job_res = JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=0,
        created_at=job.created_at
    )
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=job_res, request_id=request_id)


@router.get("/{job_id}", response_model=APIResponse[JobDetailResponse])
async def get_job_status(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Polls the status of an ongoing or completed analysis job."""
    analysis_repo = AnalysisRepository(db)
    job = await analysis_repo.get_job_by_id(job_id)
    if not job:
        raise EntityNotFoundError("AnalysisJob", job_id)

    result_schema = None
    if job.result:
        res = job.result
        conf_schema = ConfidenceScoreSchema(
            score=res.overall_confidence,
            level=res.confidence_level,
            cross_modal_agreement=res.cross_modal_agreement,
            factors=res.confidence_factors or [],
            warnings=res.warnings or []
        )
        ev_list = [
            EvidenceItemSchema(
                id=ev.id,
                evidence_type=ev.evidence_type,
                file_path=ev.file_path,
                url=ev.url,
                bbox=ev.bbox,
                geo_polygon=ev.geo_polygon,
                confidence=ev.confidence,
                description=ev.description,
                metadata=ev.metadata_json
            )
            for ev in res.evidence_items
        ]
        traces = [
            ExecutionStepTrace(
                step_order=t.step_order,
                step_name=t.step_name,
                status=t.status,
                summary=t.summary,
                details=t.details,
                duration_ms=t.duration_ms
            )
            for t in job.traces
        ]
        plan_schema = ExecutionPlanSchema.model_validate(job.query.planner_output) if job.query and job.query.planner_output else None

        result_schema = AnalysisResultSchema(
            analysis_id=res.id,
            job_id=job.id,
            status=res.status,
            query=job.query.query_text if job.query else "",
            task=job.query.task_type if job.query else "unknown",
            answer=res.answer,
            confidence=conf_schema,
            evidence=ev_list,
            execution_plan=plan_schema,
            execution_trace=traces,
            execution_duration_ms=res.execution_duration_ms,
            created_at=res.created_at
        )

    res_data = JobDetailResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        result=result_schema
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=res_data, request_id=request_id)


@router.post("/{job_id}/cancel", response_model=APIResponse[JobStatusResponse])
async def cancel_job(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Cancels a queued or executing job."""
    analysis_repo = AnalysisRepository(db)
    job = await analysis_repo.update_job_status(job_id, status="CANCELLED", error_message="Cancelled by user.")
    if not job:
        raise EntityNotFoundError("AnalysisJob", job_id)

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=JobStatusResponse.model_validate(job),
        request_id=request_id
    )
