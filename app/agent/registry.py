"""
SatQuery AI - Specialist Tool Registry
Manages tool instances, lookups, and lifecycle.
"""
from typing import Dict, List, Optional
from app.tools.base import BaseTool
from app.tools.vqa_tool import RSVQATool
from app.tools.grounding_tool import GroundingTool
from app.tools.change_tool import TemporalChangeTool
from app.tools.change_vqa_tool import ChangeVQATool
from app.tools.optical_sar_tool import OpticalSARFusionTool
from app.models.vqa_model import RSVQAAdapter
from app.models.grounding_model import RSGroundingAdapter
from app.models.change_model import RSChangeAdapter
from app.models.fusion_model import RSFusionAdapter
from app.core.logging import logger


class ToolRegistry:
    """Registry maintaining initialized specialist tool singletons."""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize_default_tools()
        return cls._instance

    def initialize_default_tools(self) -> None:
        if self._initialized:
            return

        logger.info("Initializing specialist remote sensing tools and model adapters...")
        # 1. Initialize model adapters
        vqa_adapter = RSVQAAdapter()
        grounding_adapter = RSGroundingAdapter()
        change_adapter = RSChangeAdapter()
        fusion_adapter = RSFusionAdapter()

        # 2. Register specialist tools
        self.register_tool(RSVQATool(vqa_adapter))
        self.register_tool(GroundingTool(grounding_adapter))
        self.register_tool(TemporalChangeTool(change_adapter))
        self.register_tool(ChangeVQATool(change_adapter, vqa_adapter))
        self.register_tool(OpticalSARFusionTool(fusion_adapter))

        self._initialized = True
        logger.info(f"Registered {len(self._tools)} specialist tools: {list(self._tools.keys())}")

    def register_tool(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [tool.get_info() for tool in self._tools.values()]

    def find_tools_for_task(self, task_name: str) -> List[BaseTool]:
        return [t for t in self._tools.values() if task_name in t.supported_tasks]
