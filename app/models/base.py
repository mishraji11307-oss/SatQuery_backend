"""
SatQuery AI - Base Model Adapter Interface
Defines the standard contract for all remote-sensing deep learning model adapters.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np


class BaseRemoteSensingModel(ABC):
    """Abstract interface for all remote sensing vision-language and vision models."""

    def __init__(self, model_name: str, model_path: Optional[str] = None, device: str = "cpu"):
        self.model_name = model_name
        self.model_path = model_path
        self.device = device
        self.is_loaded = False

    @abstractmethod
    def load(self) -> None:
        """Load model checkpoints and initialize weights onto target device."""
        pass

    @abstractmethod
    def predict(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute forward inference.
        inputs: dict containing image arrays, queries, masks, or metadata.
        returns: standardized output dictionary containing answers, masks, bboxes, raw confidences.
        """
        pass

    @abstractmethod
    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """Validates that provided input tensor shapes/modalities conform to model expectations."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns model architecture, backbone, parameter count, supported modalities."""
        pass
