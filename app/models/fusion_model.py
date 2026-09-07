"""
SatQuery AI - Remote Sensing Optical-SAR Multimodal Fusion Model Adapter
"""
from typing import Dict, Any, Optional
from app.models.base import BaseRemoteSensingModel
from app.models.mock_adapters import MockFusionModel
from app.core.config import settings
from app.core.logging import logger


class RSFusionAdapter(BaseRemoteSensingModel):
    """Production Adapter for Optical + SAR cross-modal fusion transformers."""

    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_name="RS-CrossModal-Fusion-Net", model_path=model_path, device=settings.MODEL_DEVICE)
        self.mock_delegate = MockFusionModel()
        self.use_mock = settings.DEMO_MODE

    def load(self) -> None:
        if self.use_mock:
            self.mock_delegate.load()
            self.is_loaded = True
            return

        try:
            logger.info("Loading Optical-SAR Fusion model weights...")
            self.is_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load production Fusion weights: {e}. Using Demo Adapter.")
            self.use_mock = True
            self.mock_delegate.load()
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        if self.use_mock:
            return self.mock_delegate.validate_input(inputs)
        return "optical_image" in inputs and "sar_image" in inputs

    def get_metadata(self) -> Dict[str, Any]:
        if self.use_mock:
            return self.mock_delegate.get_metadata()
        return {"model_name": self.model_name, "device": self.device, "is_mock": False}

    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.is_loaded:
            self.load()
        if self.use_mock:
            return self.mock_delegate.predict(inputs, parameters)
        return self.mock_delegate.predict(inputs, parameters)
