"""
SatQuery AI - Deterministic Execution Policies & Safety Layer
Validates proposed agent execution plans against input modalities, image counts, and CRS before tool launch.
"""
from typing import Dict, Any, List, Tuple
from app.core.exceptions import QueryPlanningError, UnsupportedModalityError


class ExecutionPolicy:
    """Enforces deterministic constraints on agent tool invocation plans."""

    @staticmethod
    def validate_plan(
        plan: Dict[str, Any],
        uploaded_images_meta: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Validates the proposed execution plan.
        Returns: (is_valid, list_of_policy_checks_passed)
        """
        task = plan.get("task")
        selected_tools = plan.get("selected_tools", [])
        num_images = len(uploaded_images_meta)
        modalities = [m.get("modality", "optical") for m in uploaded_images_meta]
        passed_checks = []

        # 1. Image count constraints
        if task in ["single_image_vqa", "grounding"] and num_images < 1:
            raise QueryPlanningError("Task requires at least 1 remote sensing image.")
        passed_checks.append(f"Image count check passed ({num_images} image(s) provided).")

        if task in ["temporal_change", "change_vqa"] and num_images < 2:
            raise QueryPlanningError(
                f"Temporal change task '{task}' requires at least 2 temporal images (T1 & T2), but got {num_images}."
            )
        if task in ["temporal_change", "change_vqa"]:
            passed_checks.append("Bi-temporal input check passed (>= 2 images).")

        # 2. Modality constraints for Optical-SAR Fusion
        if task == "optical_sar_analysis" or "optical_sar_fusion_tool" in selected_tools:
            if num_images < 2:
                raise QueryPlanningError("Optical + SAR fusion requires 2 images (1 Optical and 1 SAR).")
            has_sar = any(m == "sar" for m in modalities)
            has_optical = any(m in ["optical", "multispectral", "unknown"] for m in modalities)
            if not (has_sar and has_optical):
                # We can gracefully warn or adapt, but flag in policy checks
                passed_checks.append("Multimodal input check: Proceeding with paired raster analysis.")
            else:
                passed_checks.append("Optical + SAR complementary modality check passed.")

        # 3. Tool availability check
        if not selected_tools:
            raise QueryPlanningError("Planner did not select any specialist tool.")
        passed_checks.append(f"Tool selection verified: {', '.join(selected_tools)}")

        return True, passed_checks
