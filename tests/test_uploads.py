"""
SatQuery AI - Uploads & Geospatial Metadata Extraction Tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sample_data_catalog_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/data/samples")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    names = {item["name"] for item in body["data"]}
    assert {"optical_sample.png", "sar_sample.png", "t1_sample.png", "t2_sample.png"}.issubset(names)


@pytest.mark.asyncio
async def test_image_upload_and_metadata_inspection(client: AsyncClient, sample_optical_image: str):
    with open(sample_optical_image, "rb") as f:
        response = await client.post(
            "/api/v1/uploads",
            files={"file": ("sentinel2_optical.png", f, "image/png")},
            data={"modality": "optical", "tag": "t1"}
        )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] is not None
    assert data["modality"] == "optical"
    assert data["metadata"]["width"] == 256
    assert data["metadata"]["height"] == 256
    assert data["metadata"]["num_bands"] == 3

    # Retrieve individual metadata
    image_id = data["id"]
    meta_res = await client.get(f"/api/v1/uploads/{image_id}/metadata")
    assert meta_res.status_code == 200
    meta_body = meta_res.json()
    assert meta_body["data"]["width"] == 256
