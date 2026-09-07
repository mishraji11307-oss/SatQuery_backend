"""
SatQuery AI - End-to-End Analysis Pipeline Tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_single_vqa_analysis_pipeline(client: AsyncClient, sample_optical_image: str):
    # 1. Upload image
    with open(sample_optical_image, "rb") as f:
        up_res = await client.post(
            "/api/v1/uploads",
            files={"file": ("airport_optical.png", f, "image/png")},
            data={"modality": "optical"}
        )
    image_id = up_res.json()["data"]["id"]

    # 2. Submit synchronous analysis request
    analysis_res = await client.post(
        "/api/v1/analysis",
        json={
            "query": "What objects and structures are visible in this airfield?",
            "image_ids": [image_id],
            "async_mode": False
        }
    )
    assert analysis_res.status_code == 200
    res_body = analysis_res.json()
    assert res_body["success"] is True
    data = res_body["data"]
    assert data["task"] == "single_image_vqa"
    assert data["answer"] is not None
    assert data["confidence"]["score"] > 0.70
    assert len(data["execution_trace"]) >= 4


@pytest.mark.asyncio
async def test_grounding_analysis_pipeline(client: AsyncClient, sample_optical_image: str):
    with open(sample_optical_image, "rb") as f:
        up_res = await client.post(
            "/api/v1/uploads",
            files={"file": ("city.png", f, "image/png")},
            data={"modality": "optical"}
        )
    image_id = up_res.json()["data"]["id"]

    analysis_res = await client.post(
        "/api/v1/analysis",
        json={
            "query": "Where are the buildings and hangars located?",
            "image_ids": [image_id],
            "async_mode": False
        }
    )
    assert analysis_res.status_code == 200
    data = analysis_res.json()["data"]
    assert data["task"] == "grounding"
    assert any(e["evidence_type"] == "bounding_box" for e in data["evidence"])


@pytest.mark.asyncio
async def test_bitemporal_change_pipeline(client: AsyncClient, sample_optical_image: str):
    with open(sample_optical_image, "rb") as f:
        up1 = await client.post(
            "/api/v1/uploads",
            files={"file": ("t1.png", f, "image/png")},
            data={"modality": "optical", "tag": "t1"}
        )
    with open(sample_optical_image, "rb") as f:
        up2 = await client.post(
            "/api/v1/uploads",
            files={"file": ("t2.png", f, "image/png")},
            data={"modality": "optical", "tag": "t2"}
        )
    id1 = up1.json()["data"]["id"]
    id2 = up2.json()["data"]["id"]

    analysis_res = await client.post(
        "/api/v1/analysis",
        json={
            "query": "What changed between T1 and T2 imagery?",
            "image_ids": [id1, id2],
            "async_mode": False
        }
    )
    assert analysis_res.status_code == 200
    data = analysis_res.json()["data"]
    assert data["task"] == "temporal_change"
    assert any(e["evidence_type"] == "change_mask" for e in data["evidence"])
    assert any(e["evidence_type"] == "temporal_comparison" for e in data["evidence"])
