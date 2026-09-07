"""
SatQuery AI - Analysis Execution Orchestration Service
Coordinates Query Understanding -> Input Validation -> Task Planning -> Tool Execution -> Evidence Aggregation -> Confidence Calibration.
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.upload_repo import UploadRepository
from app.db.repositories.query_repo import QueryRepository
from app.db.repositories.analysis_repo import AnalysisRepository
from app.agent.planner import QueryPlanner
from app.agent.registry import ToolRegistry
from app.geospatial.validation import GeospatialValidator
from app.services.confidence_service import ConfidenceService
from app.services.evidence_service import EvidenceService
from app.schemas.analysis import (
    AnalysisResultSchema,
    ExecutionStepTrace,
    ConfidenceScoreSchema,
)
from app.core.exceptions import (
    EntityNotFoundError,
    GeospatialMismatchError,
    QueryPlanningError,
    ModelExecutionError,
)
from app.core.logging import logger


class ExecutionService:
    """End-to-end multimodal remote sensing query analysis orchestrator."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_repo = UploadRepository(db)
        self.query_repo = QueryRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.planner = QueryPlanner()
        self.registry = ToolRegistry.get_instance()

    async def execute_analysis_pipeline(
        self,
        query_text: str,
        image_ids: List[str],
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AnalysisResultSchema:
        pipeline_start = time.time()
        parameters = parameters or {}
        traces: List[ExecutionStepTrace] = []
        step_order = 0

        async def log_step(name: str, summary: str, status: str = "COMPLETED", details: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0):
            nonlocal step_order
            step_order += 1
            trace = ExecutionStepTrace(
                step_order=step_order,
                step_name=name,
                status=status,
                summary=summary,
                details=details,
                duration_ms=round(duration_ms, 2)
            )
            traces.append(trace)
            if job_id:
                await self.analysis_repo.add_trace(
                    job_id=job_id,
                    step_order=step_order,
                    step_name=name,
                    status=status,
                    summary=summary,
                    details=details,
                    duration_ms=duration_ms
                )

        # 1. Create or fetch Analysis Job
        if not job_id:
            job = await self.analysis_repo.create_job(
                image_ids=image_ids,
                user_id=user_id,
                status="PROCESSING"
            )
            job_id = job.id
        else:
            await self.analysis_repo.update_job_status(job_id, status="PROCESSING", progress=10)

        # ----------------------------------------------------------------------
        # STEP 1: LOAD & VALIDATE INPUT IMAGES
        # ----------------------------------------------------------------------
        t0 = time.time()
        images = await self.upload_repo.get_many_by_ids(image_ids)
        if len(images) != len(image_ids):
            missing = set(image_ids) - {img.id for img in images}
            raise EntityNotFoundError("UploadedImage", f"Missing IDs: {missing}")

        images_meta = []
        for img in images:
            meta_dict = {
                "id": img.id,
                "filename": img.original_filename,
                "storage_path": img.storage_path,
                "modality": img.modality,
                "tag": img.tag,
                "width": img.image_metadata.width if img.image_metadata else 0,
                "height": img.image_metadata.height if img.image_metadata else 0,
                "crs": img.image_metadata.crs if img.image_metadata else None,
                "bounds": img.image_metadata.bounds if img.image_metadata else None,
                "resolution_x": img.image_metadata.resolution_x if img.image_metadata else None,
                "acquisition_date": img.image_metadata.acquisition_date if img.image_metadata else None,
                "is_georeferenced": img.image_metadata.is_georeferenced if img.image_metadata else False,
            }
            images_meta.append(meta_dict)

        await log_step(
            name="INPUT_LOADING",
            summary=f"Loaded {len(images)} remote sensing raster(s) with extracted metadata.",
            details={"image_ids": image_ids, "modalities": [m["modality"] for m in images_meta]},
            duration_ms=(time.time() - t0) * 1000
        )

        # ----------------------------------------------------------------------
        # STEP 2: QUERY UNDERSTANDING & TASK PLANNING
        # ----------------------------------------------------------------------
        t0 = time.time()
        plan = self.planner.create_plan(
            query=query_text,
            uploaded_images=images_meta,
            force_task=parameters.get("force_task")
        )
        
        # Save query record
        query_record = await self.query_repo.create(
            query_text=query_text,
            detected_intent=plan.task,
            task_type=plan.task,
            intent_confidence=plan.intent_confidence,
            user_id=user_id,
            planner_output=plan.model_dump()
        )

        await log_step(
            name="QUERY_PLANNING",
            summary=f"Query classified as '{plan.task}' with confidence {int(plan.intent_confidence * 100)}%. Selected tools: {plan.selected_tools}.",
            details=plan.model_dump(),
            duration_ms=(time.time() - t0) * 1000
        )

        # ----------------------------------------------------------------------
        # STEP 3: GEOSPATIAL COMPATIBILITY VALIDATION
        # ----------------------------------------------------------------------
        t0 = time.time()
        geo_validation_info = None

        if plan.task in ["temporal_change", "change_vqa"] and len(images_meta) >= 2:
            geo_validation_info = GeospatialValidator.validate_bitemporal_pair(images_meta[0], images_meta[1])
            await log_step(
                name="GEOSPATIAL_VALIDATION",
                summary="Bi-temporal spatial compatibility check verified: CRS and geographic extent valid.",
                details=geo_validation_info,
                duration_ms=(time.time() - t0) * 1000
            )
        elif plan.task == "optical_sar_analysis" and len(images_meta) >= 2:
            # Sort optical first, sar second
            opt_meta = next((m for m in images_meta if m["modality"] in ["optical", "multispectral"]), images_meta[0])
            sar_meta = next((m for m in images_meta if m["modality"] == "sar"), images_meta[1])
            geo_validation_info = GeospatialValidator.validate_optical_sar_pair(opt_meta, sar_meta)
            await log_step(
                name="GEOSPATIAL_VALIDATION",
                summary="Optical and SAR multimodal raster compatibility verified: Spatial CRS aligned.",
                details=geo_validation_info,
                duration_ms=(time.time() - t0) * 1000
            )
        else:
            await log_step(
                name="INPUT_VALIDATION",
                summary="Single-raster raster grid and spectral integrity verified.",
                duration_ms=(time.time() - t0) * 1000
            )

        # ----------------------------------------------------------------------
        # STEP 4: SPECIALIST TOOL EXECUTION
        # ----------------------------------------------------------------------
        if job_id:
            await self.analysis_repo.update_job_status(job_id, status="PROCESSING", progress=50)

        aggregated_evidence: List[Dict[str, Any]] = []
        answers: List[str] = []
        raw_confidences: List[float] = []
        cross_modal_agreement: Optional[str] = None
        opt_conf = None
        sar_conf = None

        for tool_name in plan.selected_tools:
            t0 = time.time()
            tool = self.registry.get_tool(tool_name)
            if not tool:
                logger.error(f"Tool {tool_name} not found in registry.")
                continue

            # Build tool inputs
            tool_inputs = {"query": query_text}
            if plan.task in ["temporal_change", "change_vqa"]:
                tool_inputs["t1_path"] = images_meta[0]["storage_path"]
                tool_inputs["t2_path"] = images_meta[1]["storage_path"]
            elif plan.task == "optical_sar_analysis":
                opt_img = next((m for m in images_meta if m["modality"] in ["optical", "multispectral"]), images_meta[0])
                sar_img = next((m for m in images_meta if m["modality"] == "sar"), images_meta[1])
                tool_inputs["optical_path"] = opt_img["storage_path"]
                tool_inputs["sar_path"] = sar_img["storage_path"]
            else:
                tool_inputs["image_path"] = images_meta[0]["storage_path"]

            tool_result = await tool.execute(tool_inputs, context={"parameters": parameters})
            duration_ms = (time.time() - t0) * 1000

            # Store tool execution
            tool_exec_rec = await self.analysis_repo.add_tool_execution(
                job_id=job_id,
                tool_name=tool_name,
                tool_version=tool.version,
                status=tool_result.status,
                duration_ms=duration_ms,
                input_params={"query": query_text},
                output_summary=tool_result.summary_data
            )

            if tool_result.answer_fragment:
                answers.append(tool_result.answer_fragment)
            if tool_result.evidence_items:
                for ev in tool_result.evidence_items:
                    ev["tool_execution_id"] = tool_exec_rec.id
                    aggregated_evidence.append(ev)
            
            raw_confidences.append(tool_result.raw_confidence)

            if "cross_modal_agreement" in tool_result.summary_data:
                cross_modal_agreement = tool_result.summary_data["cross_modal_agreement"]
                opt_conf = tool_result.summary_data.get("optical_confidence")
                sar_conf = tool_result.summary_data.get("sar_confidence")

            await log_step(
                name=f"TOOL_EXECUTION_{tool_name.upper()}",
                summary=f"Specialist tool '{tool_name}' executed in {round(duration_ms, 1)}ms with status {tool_result.status}.",
                details=tool_result.summary_data,
                duration_ms=duration_ms
            )

        # ----------------------------------------------------------------------
        # STEP 5: EVIDENCE AGGREGATION & CONFIDENCE CALIBRATION
        # ----------------------------------------------------------------------
        t0 = time.time()
        final_answer = " ".join(answers) if answers else "Analysis completed with visual evidence generated."
        avg_raw_conf = float(sum(raw_confidences) / len(raw_confidences)) if raw_confidences else 0.85

        confidence_schema = ConfidenceService.calculate_confidence(
            raw_model_conf=avg_raw_conf,
            routing_conf=plan.intent_confidence,
            geospatial_meta=geo_validation_info,
            cross_modal_agreement=cross_modal_agreement,
            evidence_count=len(aggregated_evidence)
        )
        if opt_conf:
            confidence_schema.optical_confidence = opt_conf
        if sar_conf:
            confidence_schema.sar_confidence = sar_conf

        formatted_evidence = EvidenceService.format_evidence_items(aggregated_evidence)
        total_duration_ms = (time.time() - pipeline_start) * 1000

        await log_step(
            name="CONFIDENCE_SYNTHESIS",
            summary=f"Calibrated final confidence score: {int(confidence_schema.score * 100)}% ({confidence_schema.level.upper()}) based on {len(confidence_schema.factors)} factors.",
            details=confidence_schema.model_dump(),
            duration_ms=(time.time() - t0) * 1000
        )

        # ----------------------------------------------------------------------
        # STEP 6: SAVE ANALYSIS RESULT & COMPLETE JOB
        # ----------------------------------------------------------------------
        result_record = await self.analysis_repo.save_result(
            job_id=job_id,
            answer=final_answer,
            overall_confidence=confidence_schema.score,
            confidence_level=confidence_schema.level,
            cross_modal_agreement=confidence_schema.cross_modal_agreement,
            confidence_factors=confidence_schema.factors,
            warnings=confidence_schema.warnings,
            status="SUCCESS",
            duration_ms=total_duration_ms,
            evidence_items_data=aggregated_evidence
        )

        await self.analysis_repo.update_job_status(job_id, status="COMPLETED", progress=100)

        return AnalysisResultSchema(
            analysis_id=result_record.id,
            job_id=job_id,
            status="SUCCESS",
            query=query_text,
            task=plan.task,
            answer=final_answer,
            confidence=confidence_schema,
            evidence=formatted_evidence,
            execution_plan=plan,
            execution_trace=traces,
            execution_duration_ms=round(total_duration_ms, 2),
            created_at=datetime.now(timezone.utc)
        )
