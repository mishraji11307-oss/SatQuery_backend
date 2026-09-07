"""
SatQuery AI - Background Analysis Workers
"""
import asyncio
from typing import List, Optional, Dict, Any
from app.workers.celery_app import celery_app, _HAS_CELERY
from app.db.database import AsyncSessionLocal
from app.services.execution_service import ExecutionService
from app.db.repositories.analysis_repo import AnalysisRepository
from app.core.logging import logger


async def run_async_analysis_task(
    query_text: str,
    image_ids: List[str],
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> None:
    """Async task executor for background analysis jobs."""
    async with AsyncSessionLocal() as session:
        exec_service = ExecutionService(session)
        analysis_repo = AnalysisRepository(session)
        try:
            logger.info(f"Starting async background analysis for Job ID: {job_id}")
            await exec_service.execute_analysis_pipeline(
                query_text=query_text,
                image_ids=image_ids,
                user_id=user_id,
                job_id=job_id,
                parameters=parameters
            )
            logger.info(f"Async analysis completed successfully for Job ID: {job_id}")
        except Exception as e:
            logger.error(f"Async analysis failed for Job ID {job_id}: {e}", exc_info=True)
            if job_id:
                await analysis_repo.update_job_status(
                    job_id=job_id,
                    status="FAILED",
                    error_message=str(e)
                )


if _HAS_CELERY and celery_app:
    @celery_app.task(name="tasks.execute_remote_sensing_analysis", bind=True)
    def celery_analysis_task(
        self,
        query_text: str,
        image_ids: List[str],
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Celery synchronous wrapper for distributed background workers."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                run_async_analysis_task(
                    query_text=query_text,
                    image_ids=image_ids,
                    user_id=user_id,
                    job_id=job_id,
                    parameters=parameters
                )
            )
        finally:
            loop.close()
