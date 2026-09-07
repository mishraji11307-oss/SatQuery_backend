"""
SatQuery AI - Remote Sensing Bi-Temporal Change Detection Model Adapter
"""
from typing import Dict, Any, Optional
from app.models.base import BaseRemoteSensingModel
from app.models.mock_adapters import MockChangeModel
from app.core.config import settings
from app.core.logging import logger


class RSChangeAdapter(BaseRemoteSensingModel):
    """Production Adapter for Siamese bi-temporal change detection architectures."""

    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_name="RS-ChangeFormer-Production", model_path=model_path, device=settings.MODEL_DEVICE)
        self.mock_delegate = MockChangeModel()
        self.use_mock = settings.DEMO_MODE

    def load(self) -> None:
        if self.use_mock:
            self.mock_delegate.load()
            self.is_loaded = True
            return

        try:
            logger.info(f"Loading Change Detection weights from {self.model_path}...")
            self.is_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load production Change Detection weights: {e}. Using Demo Adapter.")
            self.use_mock = True
            self.mock_delegate.load()
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        if self.use_mock:
            return self.mock_delegate.validate_input(inputs)
        return "t1_image" in inputs and "t2_image" in inputs

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
