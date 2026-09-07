"""
SatQuery AI - Visual Grounding & Spatial Localization Tool
"""
import time
import os
import uuid
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.models.grounding_model import RSGroundingAdapter
from app.geospatial.preprocessing import RemoteSensingPreprocessor
from app.core.config import settings
from app.core.logging import logger


class GroundingTool(BaseTool):
    name: str = "grounding_tool"
    version: str = "1.0.0"
    description: str = "Localizes geospatial objects and structures from natural language, generating bounding boxes and spatial regions."
    supported_tasks: List[str] = ["grounding", "object_localization"]
    supported_modalities: List[str] = ["optical", "multispectral", "sar"]
    required_inputs: List[str] = ["image", "query"]
    required_metadata: List[str] = ["width", "height"]

    def __init__(self, model_adapter: RSGroundingAdapter):
        self.model = model_adapter

    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        return "image_path" in inputs and "query" in inputs

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        image_path = inputs.get("image_path")
        query = inputs.get("query", "")

        try:
            # 1. Load image
            img_arr = RemoteSensingPreprocessor.load_image_array(image_path)
            
            # 2. Predict grounding boxes
            model_out = self.model.predict({"image": img_arr, "query": query})
            bboxes = model_out.get("bboxes", [])
            target_label = model_out.get("target_label", "target")

            # 3. Render visual evidence overlay
            evidence_id = str(uuid.uuid4())[:8]
            artifact_filename = f"grounding_{evidence_id}.png"
            artifact_path = os.path.join(settings.EVIDENCE_DIR, artifact_filename)
            RemoteSensingPreprocessor.draw_grounding_bboxes(img_arr, bboxes, artifact_path)

            artifact_url = f"/storage/evidence/{artifact_filename}"
            exec_time = (time.time() - start_time) * 1000

            count_str = f"Found {len(bboxes)} instance(s) of '{target_label}'"
            answer = f"Visual grounding localized {len(bboxes)} target(s) matching '{query}'. Coordinates and bounding box overlays generated."

            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="SUCCESS",
                answer_fragment=answer,
                raw_confidence=model_out.get("raw_confidence", 0.92),
                execution_time_ms=round(exec_time, 2),
                summary_data={
                    "target_label": target_label,
                    "count": len(bboxes),
                    "model": model_out.get("model_name")
                },
                evidence_items=[{
                    "evidence_type": "bounding_box",
                    "file_path": artifact_path,
                    "url": artifact_url,
                    "source_tool": self.name,
                    "confidence": model_out.get("raw_confidence", 0.92),
                    "description": f"Grounding detection overlay highlighting {count_str}",
                    "bboxes": bboxes,
                    "metadata": {"bounding_boxes": bboxes, "count": len(bboxes)}
                }]
            )
        except Exception as e:
            logger.error(f"GroundingTool failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="FAILED",
                error=str(e),
                raw_confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000
            )
