"""
SatQuery AI - Single-Image Remote Sensing VQA Tool
"""
import time
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.models.vqa_model import RSVQAAdapter
from app.geospatial.preprocessing import RemoteSensingPreprocessor
from app.core.logging import logger


class RSVQATool(BaseTool):
    name: str = "vqa_tool"
    version: str = "1.0.0"
    description: str = "Performs visual question answering and scene interpretation on single remote sensing rasters."
    supported_tasks: List[str] = ["single_image_vqa", "scene_classification", "counting"]
    supported_modalities: List[str] = ["optical", "multispectral", "sar"]
    required_inputs: List[str] = ["image", "query"]
    required_metadata: List[str] = ["width", "height"]

    def __init__(self, model_adapter: RSVQAAdapter):
        self.model = model_adapter

    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        return "image_path" in inputs and "query" in inputs

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        image_path = inputs.get("image_path")
        query = inputs.get("query", "")

        try:
            # Load and preprocess image
            img_arr = RemoteSensingPreprocessor.load_image_array(image_path)
            
            # Predict
            model_out = self.model.predict({"image": img_arr, "query": query})
            exec_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="SUCCESS",
                answer_fragment=model_out.get("answer"),
                raw_confidence=model_out.get("raw_confidence", 0.90),
                execution_time_ms=round(exec_time, 2),
                summary_data={"model": model_out.get("model_name"), "query": query},
                evidence_items=[{
                    "evidence_type": "scene_interpretation",
                    "source_tool": self.name,
                    "confidence": model_out.get("raw_confidence", 0.90),
                    "description": model_out.get("answer"),
                    "metadata": {"sensor_mode": "optical_vqa"}
                }]
            )
        except Exception as e:
            logger.error(f"RSVQATool execution failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="FAILED",
                error=str(e),
                raw_confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000
            )
