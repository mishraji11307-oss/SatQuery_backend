"""
SatQuery AI - Optical + SAR Multimodal Fusion Specialist Tool
"""
import time
import os
import uuid
from typing import Dict, Any, List
from app.tools.base import BaseTool, ToolResult
from app.models.fusion_model import RSFusionAdapter
from app.geospatial.registration import ImageRegistrar
from app.geospatial.preprocessing import RemoteSensingPreprocessor
from app.core.config import settings
from app.core.logging import logger


class OpticalSARFusionTool(BaseTool):
    name: str = "optical_sar_fusion_tool"
    version: str = "1.0.0"
    description: str = "Performs cross-modal fusion between Optical multispectral reflectance and SAR polarimetric microwave backscatter."
    supported_tasks: List[str] = ["optical_sar_analysis", "cross_modal_fusion", "all_weather_monitoring"]
    supported_modalities: List[str] = ["optical", "sar"]
    required_inputs: List[str] = ["optical_image", "sar_image"]
    required_metadata: List[str] = ["modality", "crs"]

    def __init__(self, model_adapter: RSFusionAdapter):
        self.model = model_adapter

    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        return "optical_path" in inputs and "sar_path" in inputs

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        optical_path = inputs.get("optical_path")
        sar_path = inputs.get("sar_path")
        query = inputs.get("query", "")

        try:
            # 1. Load optical RGB array
            opt_arr = RemoteSensingPreprocessor.load_image_array(optical_path)

            # 2. Load & preprocess SAR (dB scaling + speckle filter)
            sar_raw = RemoteSensingPreprocessor.load_image_array(sar_path)
            sar_processed = RemoteSensingPreprocessor.preprocess_sar(sar_raw)

            # 3. Coregister SAR onto Optical geometry
            aligned_sar, reg_meta = ImageRegistrar.align_images(opt_arr, sar_processed, method="orb")

            # 4. Predict fused representation
            model_out = self.model.predict({
                "optical_image": opt_arr,
                "sar_image": aligned_sar,
                "query": query
            })

            # 5. Create cross-modal side-by-side artifact
            unique_id = str(uuid.uuid4())[:8]
            comp_filename = f"opt_sar_comparison_{unique_id}.png"
            comp_path = os.path.join(settings.EVIDENCE_DIR, comp_filename)
            RemoteSensingPreprocessor.create_side_by_side(
                opt_arr, aligned_sar, comp_path,
                label1="Optical Multispectral", label2="SAR Backscatter (dB)"
            )

            exec_time = (time.time() - start_time) * 1000
            answer = model_out.get("fused_summary")

            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="SUCCESS",
                answer_fragment=answer,
                raw_confidence=model_out.get("fusion_score", 0.91),
                execution_time_ms=round(exec_time, 2),
                summary_data={
                    "optical_confidence": model_out.get("optical_confidence"),
                    "sar_confidence": model_out.get("sar_confidence"),
                    "cross_modal_agreement": model_out.get("cross_modal_agreement"),
                    "findings": model_out.get("findings", [])
                },
                evidence_items=[
                    {
                        "evidence_type": "optical_evidence",
                        "source_tool": self.name,
                        "confidence": model_out.get("optical_confidence", 0.89),
                        "description": "Optical sensor confirms visible spectral signatures and surface albedo.",
                        "metadata": {"modality": "optical"}
                    },
                    {
                        "evidence_type": "sar_evidence",
                        "source_tool": self.name,
                        "confidence": model_out.get("sar_confidence", 0.92),
                        "description": "SAR microwave backscatter confirms structural roughness and penetration of cloud veil.",
                        "metadata": {"modality": "sar", "speckle_filtered": True}
                    },
                    {
                        "evidence_type": "fused_comparison",
                        "file_path": comp_path,
                        "url": f"/storage/evidence/{comp_filename}",
                        "source_tool": self.name,
                        "confidence": model_out.get("fusion_score", 0.91),
                        "description": "Cross-modal Optical vs SAR coregistered side-by-side evidence.",
                        "metadata": {"agreement": model_out.get("cross_modal_agreement")}
                    }
                ]
            )
        except Exception as e:
            logger.error(f"OpticalSARFusionTool failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                tool_version=self.version,
                status="FAILED",
                error=str(e),
                raw_confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000
            )
