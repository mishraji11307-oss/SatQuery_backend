"""
SatQuery AI - Analysis Execution APIs
"""
from typing import Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, Request, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.analysis_repo import AnalysisRepository
from app.db.models import User
from app.services.execution_service import ExecutionService
from app.schemas.response import APIResponse
from app.schemas.analysis import AnalysisRequest, AnalysisResultSchema, ConfidenceScoreSchema, ExecutionPlanSchema, ExecutionStepTrace
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.job import JobStatusResponse
from app.api.dependencies import get_optional_user
from app.workers.analysis_tasks import run_async_analysis_task
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/analysis", tags=["Analysis & Reasoning"])


@router.post("", response_model=APIResponse[Union[AnalysisResultSchema, JobStatusResponse]], status_code=status.HTTP_200_OK)
async def submit_analysis(
    req: AnalysisRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an Earth Observation analysis request.
    Executes synchronous analysis by default, or returns job_id if async_mode is true.
    """
    user_id = current_user.id if current_user else None
    request_id = getattr(request.state, "request_id", "unknown")

    if req.async_mode:
        # Asynchronous background job path
        analysis_repo = AnalysisRepository(db)
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
        return APIResponse(success=True, data=job_res, request_id=request_id)

    # Synchronous execution path
    exec_service = ExecutionService(db)
    result = await exec_service.execute_analysis_pipeline(
        query_text=req.query,
        image_ids=req.image_ids,
        user_id=user_id,
        parameters=req.parameters
    )

    return APIResponse(success=True, data=result, request_id=request_id)


@router.get("/{analysis_id}", response_model=APIResponse[AnalysisResultSchema])
async def get_analysis_by_id(
    analysis_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full analysis result, confidence factors, visual evidence, and execution trace."""
    analysis_repo = AnalysisRepository(db)
    # Search by analysis result ID or job ID
    job = await analysis_repo.get_job_by_id(analysis_id)
    if not job or not job.result:
        raise EntityNotFoundError("AnalysisResult", analysis_id)

    res = job.result
    conf_schema = ConfidenceScoreSchema(
        score=res.overall_confidence,
        level=res.confidence_level,
        cross_modal_agreement=res.cross_modal_agreement,
        factors=res.confidence_factors or [],
        warnings=res.warnings or []
    )

    ev_list = []
    for ev in res.evidence_items:
        ev_list.append(
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
        )

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

    plan_schema = None
    if job.query and job.query.planner_output:
        plan_schema = ExecutionPlanSchema.model_validate(job.query.planner_output)

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

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=result_schema, request_id=request_id)
