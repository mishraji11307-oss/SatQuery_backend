"""
SatQuery AI - Agentic Query Planner
Constructs validated, auditable execution plans for Earth Observation tasks.
"""
from typing import Dict, Any, List, Optional
from app.agent.router import QueryRouter
from app.agent.policies import ExecutionPolicy
from app.agent.registry import ToolRegistry
from app.schemas.analysis import ExecutionPlanSchema
from app.core.exceptions import QueryPlanningError
from app.core.logging import logger


class QueryPlanner:
    """Orchestrates query understanding, tool selection, and deterministic validation."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry.get_instance()

    def create_plan(
        self,
        query: str,
        uploaded_images: List[Dict[str, Any]],
        force_task: Optional[str] = None
    ) -> ExecutionPlanSchema:
        """
        Creates a structured, policy-validated execution plan.
        """
        num_images = len(uploaded_images)
        image_ids = [img.get("id") for img in uploaded_images]
        modalities = [img.get("modality", "optical") for img in uploaded_images]

        # 1. Route Intent
        routing_info = QueryRouter.route_query(
            query=query,
            num_images=num_images,
            modalities=modalities
        )
        task = force_task or routing_info.get("suggested_task", "single_image_vqa")
        intent_conf = routing_info.get("confidence", 1.0)

        # 2. Specialist Tool Selection
        selected_tools = []
        requires_registration = False
        requires_optical_sar_fusion = False

        if task == "grounding":
            selected_tools = ["grounding_tool"]
        elif task == "temporal_change":
            selected_tools = ["change_detection_tool", "change_vqa_tool"]
            requires_registration = True
        elif task == "change_vqa":
            selected_tools = ["change_vqa_tool", "change_detection_tool"]
            requires_registration = True
        elif task == "optical_sar_analysis":
            selected_tools = ["optical_sar_fusion_tool"]
            requires_optical_sar_fusion = True
            requires_registration = True
        elif task == "single_image_vqa":
            selected_tools = ["vqa_tool"]
        elif task == "metadata_query":
            selected_tools = ["vqa_tool"]
        else:
            selected_tools = ["vqa_tool"]

        raw_plan = {
            "task": task,
            "selected_tools": selected_tools,
            "input_image_ids": image_ids,
            "input_modalities": modalities,
            "requires_registration": requires_registration,
            "requires_optical_sar_fusion": requires_optical_sar_fusion
        }

        # 3. Apply Deterministic Safety Policies
        is_valid, policy_checks = ExecutionPolicy.validate_plan(raw_plan, uploaded_images)

        plan = ExecutionPlanSchema(
            task=task,
            intent_confidence=intent_conf,
            selected_tools=selected_tools,
            input_image_ids=image_ids,
            input_modalities=modalities,
            requires_registration=requires_registration,
            requires_optical_sar_fusion=requires_optical_sar_fusion,
            validation_status="VALIDATED" if is_valid else "FAILED",
            policy_checks=policy_checks
        )

        logger.info(f"Generated Execution Plan: task='{task}', tools={selected_tools}")
        return plan
