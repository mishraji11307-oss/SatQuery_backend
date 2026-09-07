"""
SatQuery AI - Analysis Job, Results, Evidence & Traces Repository
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models import (
    AnalysisJob,
    ToolExecution,
    AnalysisResult,
    EvidenceItem,
    ExecutionTrace
)


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        image_ids: List[str],
        query_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = "QUEUED"
    ) -> AnalysisJob:
        job = AnalysisJob(
            user_id=user_id,
            query_id=query_id,
            image_ids=image_ids,
            status=status,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job_by_id(self, job_id: str) -> Optional[AnalysisJob]:
        result = await self.db.execute(
            select(AnalysisJob)
            .options(
                selectinload(AnalysisJob.query),
                selectinload(AnalysisJob.result).selectinload(AnalysisResult.evidence_items),
                selectinload(AnalysisJob.tool_executions),
                selectinload(AnalysisJob.traces)
            )
            .where(AnalysisJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        error_message: Optional[str] = None
    ) -> Optional[AnalysisJob]:
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        job.status = status
        job.progress = progress
        if error_message:
            job.error_message = error_message
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            job.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def add_trace(
        self,
        job_id: str,
        step_order: int,
        step_name: str,
        summary: str,
        status: str = "COMPLETED",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0
    ) -> ExecutionTrace:
        trace = ExecutionTrace(
            job_id=job_id,
            step_order=step_order,
            step_name=step_name,
            status=status,
            summary=summary,
            details=details,
            duration_ms=duration_ms
        )
        self.db.add(trace)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def add_tool_execution(
        self,
        job_id: str,
        tool_name: str,
        tool_version: str = "1.0.0",
        model_name: Optional[str] = None,
        status: str = "SUCCESS",
        duration_ms: float = 0.0,
        input_params: Optional[Dict[str, Any]] = None,
        output_summary: Optional[Dict[str, Any]] = None
    ) -> ToolExecution:
        exec_item = ToolExecution(
            job_id=job_id,
            tool_name=tool_name,
            tool_version=tool_version,
            model_name=model_name,
            status=status,
            duration_ms=duration_ms,
            input_parameters=input_params,
            output_summary=output_summary
        )
        self.db.add(exec_item)
        await self.db.commit()
        await self.db.refresh(exec_item)
        return exec_item

    async def save_result(
        self,
        job_id: str,
        answer: Optional[str],
        overall_confidence: float,
        confidence_level: str,
        cross_modal_agreement: Optional[str] = None,
        confidence_factors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        status: str = "SUCCESS",
        duration_ms: float = 0.0,
        evidence_items_data: Optional[List[Dict[str, Any]]] = None
    ) -> AnalysisResult:
        result = AnalysisResult(
            job_id=job_id,
            answer=answer,
            status=status,
            overall_confidence=overall_confidence,
            confidence_level=confidence_level,
            cross_modal_agreement=cross_modal_agreement,
            confidence_factors=confidence_factors or [],
            warnings=warnings or [],
            execution_duration_ms=duration_ms
        )
        self.db.add(result)
        await self.db.flush()

        if evidence_items_data:
            for item in evidence_items_data:
                ev = EvidenceItem(
                    result_id=result.id,
                    tool_execution_id=item.get("tool_execution_id"),
                    evidence_type=item.get("evidence_type", "model_output"),
                    file_path=item.get("file_path"),
                    url=item.get("url"),
                    bbox=item.get("bbox"),
                    geo_polygon=item.get("geo_polygon"),
                    confidence=item.get("confidence", 1.0),
                    description=item.get("description"),
                    metadata_json=item.get("metadata_json")
                )
                self.db.add(ev)

        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def list_recent_jobs(self, user_id: Optional[str] = None, limit: int = 50) -> List[AnalysisJob]:
        query = (
            select(AnalysisJob)
            .options(
                selectinload(AnalysisJob.query),
                selectinload(AnalysisJob.result).selectinload(AnalysisResult.evidence_items),
                selectinload(AnalysisJob.traces)
            )
        )
        if user_id:
            query = query.where(AnalysisJob.user_id == user_id)
        query = query.order_by(AnalysisJob.created_at.desc()).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())
