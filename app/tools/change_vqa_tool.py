"""
SatQuery AI - Bi-Temporal Change-VQA Specialist Tool
"""
import time
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.models.change_model import RSChangeAdapter
from app.models.vqa_model import RSVQAAdapter
from app.geospatial.preprocessing import RemoteSensingPreprocessor
from app.core.logging import logger


class ChangeVQATool(BaseTool):
    name: str = "change_vqa_tool"
    version: str = "1.0.0"
    description: str = "Answers natural language questions about temporal evolution between two remote sensing scenes."
    supported_tasks: List[str] = ["change_vqa", "temporal_qa"]
    supported_modalities: List[str] = ["optical", "multispectral", "sar"]
    required_inputs: List[str] = ["t1_image", "t2_image", "query"]
    required_metadata: List[str] = ["crs"]

    def __init__(self, change_adapter: RSChangeAdapter, vqa_adapter: RSVQAAdapter):
        self.change_model = change_adapter
        self.vqa_model = vqa_adapter

    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        return "t1_path" in inputs and "t2_path" in inputs and "query" in inputs

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        t1_path = inputs.get("t1_path")
        t2_path = inputs.get("t2_path")
        query = inputs.get("query", "")

        try:
            t1_arr = RemoteSensingPreprocessor.load_image_array(t1_path)
            t2_arr = RemoteSensingPreprocessor.load_image_array(t2_path)

            # Change reasoning
            change_out = self.change_model.predict({"t1_image": t1_arr, "t2_image": t2_arr})
            exec_time = (time.time() - start_time) * 1000

            answer = (
                f"Regarding '{query}': Comparison indicates direct evidence of {change_out.get('primary_change_class', 'surface variation')}. "
                f"{change_out.get('description', '')}"
            )

            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="SUCCESS",
                answer_fragment=answer,
                raw_confidence=change_out.get("raw_confidence", 0.90),
                execution_time_ms=round(exec_time, 2),
                summary_data={"query": query, "model": self.change_model.model_name},
                evidence_items=[{
                    "evidence_type": "change_vqa_summary",
                    "source_tool": self.name,
                    "confidence": change_out.get("raw_confidence", 0.90),
                    "description": answer,
                    "metadata": {"task": "change_vqa"}
                }]
            )
        except Exception as e:
            logger.error(f"ChangeVQATool failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="FAILED",
                error=str(e),
                raw_confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000
            )
