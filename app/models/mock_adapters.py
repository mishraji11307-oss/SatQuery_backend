"""
SatQuery AI - High-Fidelity Mock Adapters (Demo Mode)
Provides realistic, deterministic remote sensing domain outputs when heavyweight GPU checkpoints are not mounted.
"""
import time
import numpy as np
from typing import Dict, Any, Optional, List
from app.models.base import BaseRemoteSensingModel
from app.core.config import settings
from app.core.logging import logger


class MockVQAModel(BaseRemoteSensingModel):
    def __init__(self):
        super().__init__(model_name="RS-VQA-GeoCLIP-ViT-L", device=settings.MODEL_DEVICE)

    def load(self) -> None:
        self.is_loaded = True
        logger.info("MockVQAModel loaded into memory.")

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        return "image" in inputs and "query" in inputs

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backbone": "Vision-Language Transformer (Remote Sensing fine-tuned)",
            "adapter_type": "MOCK_DEMO" if settings.DEMO_MODE else "PRODUCTION",
            "supported_tasks": ["single_image_vqa", "scene_classification", "counting"]
        }

    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if settings.MOCK_MODEL_LATENCY > 0:
            time.sleep(settings.MOCK_MODEL_LATENCY)

        query = inputs.get("query", "").lower()
        image = inputs.get("image")
        
        # Domain-aware contextual answer generation
        if any(k in query for k in ["runway", "airport", "aircraft", "airplane"]):
            answer = "The scene captures an airfield complex with 2 visible taxiways and approximately 4 commercial aircraft parked in tarmac bays."
            raw_conf = 0.94
        elif any(k in query for k in ["building", "structure", "urban", "city", "houses"]):
            answer = "High-density urban development observed with structured rectangular residential blocks and paved transit corridors."
            raw_conf = 0.91
        elif any(k in query for k in ["water", "river", "lake", "ocean", "flood"]):
            answer = "Prominent water body identified with low spectral reflectance in near-infrared, indicative of an inland reservoir or river channel."
            raw_conf = 0.96
        elif any(k in query for k in ["vegetation", "forest", "crop", "agriculture", "trees"]):
            answer = "Extensive vegetative canopy exhibiting high NDVI spectral signature, characteristic of healthy agricultural farmland."
            raw_conf = 0.93
        elif any(k in query for k in ["solar", "panel", "energy", "renewable"]):
            answer = "Photovoltaic solar array identified with high-contrast rectilinear cell arrangements aligned south-facing."
            raw_conf = 0.92
        else:
            answer = "Remote sensing scene analysis indicates a mixed-use landscape featuring built infrastructure, road networks, and peripheral green zones."
            raw_conf = 0.88

        return {
            "answer": answer,
            "raw_confidence": raw_conf,
            "model_name": self.model_name,
            "is_mock": True
        }


class MockGroundingModel(BaseRemoteSensingModel):
    def __init__(self):
        super().__init__(model_name="RS-GroundingDINO-SwinB", device=settings.MODEL_DEVICE)

    def load(self) -> None:
        self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        return "image" in inputs and "query" in inputs

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backbone": "Open-Vocabulary Grounding Swin-Base",
            "adapter_type": "MOCK_DEMO" if settings.DEMO_MODE else "PRODUCTION"
        }

    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if settings.MOCK_MODEL_LATENCY > 0:
            time.sleep(settings.MOCK_MODEL_LATENCY)

        query = inputs.get("query", "").lower()
        
        # Generate spatial bounding boxes [ymin, xmin, ymax, xmax] in 0..1 coordinates
        if any(k in query for k in ["building", "structure", "house"]):
            target_label = "building"
            bboxes = [
                {"label": "building", "confidence": 0.94, "box_2d": [0.15, 0.20, 0.38, 0.45]},
                {"label": "building", "confidence": 0.91, "box_2d": [0.42, 0.18, 0.65, 0.42]},
                {"label": "building", "confidence": 0.89, "box_2d": [0.22, 0.55, 0.48, 0.82]},
                {"label": "industrial_shed", "confidence": 0.87, "box_2d": [0.58, 0.52, 0.85, 0.88]},
            ]
        elif any(k in query for k in ["aircraft", "plane", "airplane"]):
            target_label = "aircraft"
            bboxes = [
                {"label": "aircraft", "confidence": 0.96, "box_2d": [0.25, 0.30, 0.42, 0.48]},
                {"label": "aircraft", "confidence": 0.93, "box_2d": [0.50, 0.35, 0.68, 0.52]},
            ]
        elif any(k in query for k in ["ship", "vessel", "boat"]):
            target_label = "maritime_vessel"
            bboxes = [
                {"label": "cargo_vessel", "confidence": 0.95, "box_2d": [0.30, 0.40, 0.55, 0.62]},
                {"label": "patrol_boat", "confidence": 0.88, "box_2d": [0.65, 0.20, 0.78, 0.35]},
            ]
        elif any(k in query for k in ["solar", "panel", "array"]):
            target_label = "solar_array"
            bboxes = [
                {"label": "solar_panel_block_A", "confidence": 0.97, "box_2d": [0.18, 0.15, 0.52, 0.50]},
                {"label": "solar_panel_block_B", "confidence": 0.94, "box_2d": [0.55, 0.20, 0.88, 0.60]},
            ]
        else:
            target_label = "detected_region"
            bboxes = [
                {"label": "region_of_interest_1", "confidence": 0.88, "box_2d": [0.20, 0.20, 0.50, 0.50]},
                {"label": "region_of_interest_2", "confidence": 0.85, "box_2d": [0.55, 0.55, 0.85, 0.85]},
            ]

        return {
            "target_label": target_label,
            "bboxes": bboxes,
            "total_count": len(bboxes),
            "raw_confidence": float(np.mean([b["confidence"] for b in bboxes])),
            "model_name": self.model_name,
            "is_mock": True
        }


class MockChangeModel(BaseRemoteSensingModel):
    def __init__(self):
        super().__init__(model_name="RS-ChangeFormer-V2", device=settings.MODEL_DEVICE)

    def load(self) -> None:
        self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        return "t1_image" in inputs and "t2_image" in inputs

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backbone": "Hierarchical Dual-Branch Siamese Transformer",
            "adapter_type": "MOCK_DEMO" if settings.DEMO_MODE else "PRODUCTION"
        }

    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if settings.MOCK_MODEL_LATENCY > 0:
            time.sleep(settings.MOCK_MODEL_LATENCY)

        return {
            "change_detected": True,
            "primary_change_class": "urban_expansion_and_infrastructure",
            "description": "Bi-temporal analysis shows significant structural additions in the southeastern sector, including newly built foundations and road clearance.",
            "raw_confidence": 0.92,
            "model_name": self.model_name,
            "is_mock": True
        }


class MockFusionModel(BaseRemoteSensingModel):
    def __init__(self):
        super().__init__(model_name="RS-CrossModal-OptSAR-Net", device=settings.MODEL_DEVICE)

    def load(self) -> None:
        self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        return "optical_image" in inputs and "sar_image" in inputs

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backbone": "Optical-SAR Cross-Attention Fusion Transformer",
            "adapter_type": "MOCK_DEMO" if settings.DEMO_MODE else "PRODUCTION"
        }

    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if settings.MOCK_MODEL_LATENCY > 0:
            time.sleep(settings.MOCK_MODEL_LATENCY)

        query = inputs.get("query", "").lower()
        
        # Real remote-sensing insight: SAR penetrates clouds & detects corner reflectors (dielectric metal / roughness),
        # Optical captures spectral albedo and true color reflection.
        optical_conf = 0.89
        sar_conf = 0.92
        agreement = "high"
        
        findings = [
            "Optical sensor confirms surface spectral signature and natural boundary definitions.",
            "SAR C-band radar backscatter indicates strong double-bounce reflections typical of vertical metallic structures and building edges.",
            "Synthetic Aperture Radar successfully penetrates partial cloud cover in northeast quadrant where optical reflectance was diffused."
        ]

        fused_summary = (
            "Multimodal Optical + SAR fusion validates structural targets across both sensors. "
            "SAR backscatter confirms dense metallic/concrete materials with high dielectric constant, "
            "while optical reflectance confirms active facility zoning. Modality agreement is High."
        )

        return {
            "fused_summary": fused_summary,
            "optical_confidence": optical_conf,
            "sar_confidence": sar_conf,
            "cross_modal_agreement": agreement,
            "fusion_score": 0.91,
            "findings": findings,
            "model_name": self.model_name,
            "is_mock": True
        }
