"""
SatQuery AI - Bi-Temporal Change Detection Specialist Tool
"""
import time
import os
import uuid
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.models.change_model import RSChangeAdapter
from app.geospatial.registration import ImageRegistrar
from app.geospatial.preprocessing import RemoteSensingPreprocessor
from app.core.config import settings
from app.core.logging import logger


class TemporalChangeTool(BaseTool):
    name: str = "change_detection_tool"
    version: str = "1.0.0"
    description: str = "Performs pixel-level and semantic bi-temporal change detection between T1 and T2 satellite acquisitions."
    supported_tasks: List[str] = ["temporal_change", "change_detection", "urban_expansion", "deforestation"]
    supported_modalities: List[str] = ["optical", "multispectral", "sar"]
    required_inputs: List[str] = ["t1_image", "t2_image"]
    required_metadata: List[str] = ["crs", "bounds"]

    def __init__(self, model_adapter: RSChangeAdapter):
        self.model = model_adapter

    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        return "t1_path" in inputs and "t2_path" in inputs

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        t1_path = inputs.get("t1_path")
        t2_path = inputs.get("t2_path")
        query = inputs.get("query", "")

        try:
            # 1. Load both rasters
            t1_arr = RemoteSensingPreprocessor.load_image_array(t1_path)
            t2_arr = RemoteSensingPreprocessor.load_image_array(t2_path)

            # 2. Geometric alignment / Coregistration
            aligned_t2, reg_meta = ImageRegistrar.align_images(t1_arr, t2_arr, method="ecc")

            # 3. Model prediction
            model_out = self.model.predict({"t1_image": t1_arr, "t2_image": aligned_t2})

            # 4. Generate visual change mask overlay artifact
            unique_id = str(uuid.uuid4())[:8]
            mask_filename = f"change_mask_{unique_id}.png"
            mask_path = os.path.join(settings.EVIDENCE_DIR, mask_filename)
            _, change_pct, _ = RemoteSensingPreprocessor.create_change_mask_artifact(
                t1_arr, aligned_t2, mask_path, threshold=30.0
            )

            # 5. Generate side-by-side comparison artifact
            comp_filename = f"comparison_{unique_id}.png"
            comp_path = os.path.join(settings.EVIDENCE_DIR, comp_filename)
            RemoteSensingPreprocessor.create_side_by_side(
                t1_arr, aligned_t2, comp_path, label1="T1 (Baseline)", label2="T2 (Latest)"
            )

            exec_time = (time.time() - start_time) * 1000
            answer = (
                f"Bi-temporal change analysis identified {change_pct}% altered area between acquisitions. "
                f"{model_out.get('description', '')}"
            )

            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="SUCCESS",
                answer_fragment=answer,
                raw_confidence=model_out.get("raw_confidence", 0.91),
                execution_time_ms=round(exec_time, 2),
                summary_data={
                    "change_percentage": change_pct,
                    "primary_class": model_out.get("primary_change_class"),
                    "registration_status": reg_meta.get("status"),
                    "correlation_score": reg_meta.get("correlation_score")
                },
                evidence_items=[
                    {
                        "evidence_type": "change_mask",
                        "file_path": mask_path,
                        "url": f"/storage/evidence/{mask_filename}",
                        "source_tool": self.name,
                        "confidence": model_out.get("raw_confidence", 0.91),
                        "description": f"Binary/Spectral change mask overlay indicating {change_pct}% area alteration.",
                        "metadata": {"change_percentage": change_pct, "threshold": 30.0}
                    },
                    {
                        "evidence_type": "temporal_comparison",
                        "file_path": comp_path,
                        "url": f"/storage/evidence/{comp_filename}",
                        "source_tool": self.name,
                        "confidence": 0.95,
                        "description": "Side-by-side T1 baseline and T2 coregistered comparison.",
                        "metadata": {"registration": reg_meta}
                    }
                ]
            )
        except Exception as e:
            logger.error(f"TemporalChangeTool execution failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="FAILED",
                error=str(e),
                raw_confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000
            )
