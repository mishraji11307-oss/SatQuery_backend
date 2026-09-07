"""
SatQuery AI - Specialist Tools Introspection APIs
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Request
from app.agent.registry import ToolRegistry
from app.schemas.response import APIResponse
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/tools", tags=["Tools Registry"])


@router.get("", response_model=APIResponse[List[Dict[str, Any]]])
async def list_available_tools(request: Request):
    """Lists all registered specialist tools, supported modalities and tasks."""
    registry = ToolRegistry.get_instance()
    tools_list = registry.list_tools()
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=tools_list, request_id=request_id)


@router.get("/{tool_name}", response_model=APIResponse[Dict[str, Any]])
async def get_tool_details(tool_name: str, request: Request):
    """Retrieves operational specification for a specialist tool."""
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool(tool_name)
    if not tool:
        raise EntityNotFoundError("Tool", tool_name)

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=tool.get_info(), request_id=request_id)
