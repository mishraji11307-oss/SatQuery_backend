"""
SatQuery AI - Analysis History & Audit Trail APIs
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.analysis_repo import AnalysisRepository
from app.db.models import User
from app.schemas.response import APIResponse
from app.schemas.analysis import AnalysisResultSchema, ConfidenceScoreSchema, ExecutionPlanSchema, ExecutionStepTrace
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.job import JobDetailResponse
from app.api.dependencies import get_optional_user

router = APIRouter(prefix="/history", tags=["Analysis History"])


@router.get("", response_model=APIResponse[List[JobDetailResponse]])
async def get_analysis_history(
    request: Request,
    limit: int = 20,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological history of Earth Observation analyses."""
    analysis_repo = AnalysisRepository(db)
    user_id = current_user.id if current_user else None
    jobs = await analysis_repo.list_recent_jobs(user_id=user_id, limit=limit)

    results_list: List[JobDetailResponse] = []
    for job in jobs:
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
            plan_schema = (
                ExecutionPlanSchema.model_validate(job.query.planner_output)
                if job.query and job.query.planner_output
                else None
            )

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

        results_list.append(
            JobDetailResponse(
                job_id=job.id,
                status=job.status,
                progress=job.progress,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at,
                created_at=job.created_at,
                result=result_schema
            )
        )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=results_list, request_id=request_id)
