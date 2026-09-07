"""
SatQuery AI - Specialist Tools Tests
"""
import pytest
from app.agent.registry import ToolRegistry


@pytest.mark.asyncio
async def test_vqa_tool_execution(sample_optical_image: str):
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool("vqa_tool")
    assert tool is not None

    result = await tool.execute(
        {"image_path": sample_optical_image, "query": "What objects are present?"},
        context={}
    )
    assert result.status == "SUCCESS"
    assert result.answer_fragment is not None
    assert result.raw_confidence >= 0.80
    assert len(result.evidence_items) > 0


@pytest.mark.asyncio
async def test_grounding_tool_execution(sample_optical_image: str):
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool("grounding_tool")
    assert tool is not None

    result = await tool.execute(
        {"image_path": sample_optical_image, "query": "Where are the buildings?"},
        context={}
    )
    assert result.status == "SUCCESS"
    assert len(result.evidence_items) > 0
    assert result.evidence_items[0]["evidence_type"] == "bounding_box"
    assert len(result.evidence_items[0]["bboxes"]) > 0


@pytest.mark.asyncio
async def test_temporal_change_tool_execution(sample_optical_image: str):
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool("change_detection_tool")
    assert tool is not None

    result = await tool.execute(
        {"t1_path": sample_optical_image, "t2_path": sample_optical_image, "query": "What changed?"},
        context={}
    )
    assert result.status == "SUCCESS"
    assert "change_percentage" in result.summary_data
    assert any(e["evidence_type"] == "change_mask" for e in result.evidence_items)


@pytest.mark.asyncio
async def test_optical_sar_fusion_tool_execution(sample_optical_image: str, sample_sar_image: str):
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool("optical_sar_fusion_tool")
    assert tool is not None

    result = await tool.execute(
        {
            "optical_path": sample_optical_image,
            "sar_path": sample_sar_image,
            "query": "Compare optical and SAR sensor observations"
        },
        context={}
    )
    assert result.status == "SUCCESS"
    assert "cross_modal_agreement" in result.summary_data
    assert any(e["evidence_type"] == "sar_evidence" for e in result.evidence_items)
