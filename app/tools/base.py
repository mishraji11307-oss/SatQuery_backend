"""
SatQuery AI - Specialist Tool Contract & Base Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str
    tool_version: str = "1.0.0"
    status: str = "SUCCESS"  # SUCCESS, FAILED, INSUFFICIENT_EVIDENCE
    answer_fragment: Optional[str] = None
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    raw_confidence: float = 1.0
    execution_time_ms: float = 0.0
    summary_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all Earth Observation specialist tools."""

    name: str
    version: str = "1.0.0"
    description: str
    supported_tasks: List[str]
    supported_modalities: List[str]
    required_inputs: List[str]
    required_metadata: List[str]

    @abstractmethod
    def validate(self, inputs: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Validates that provided images and metadata meet the tool's requirements."""
        pass

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Executes the specialized remote sensing workflow."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Returns introspective metadata about this tool."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "supported_tasks": self.supported_tasks,
            "supported_modalities": self.supported_modalities,
            "required_inputs": self.required_inputs,
            "required_metadata": self.required_metadata,
        }
