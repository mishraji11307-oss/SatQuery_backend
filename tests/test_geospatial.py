"""
SatQuery AI - Geospatial Validation & Registration Tests
"""
import pytest
from app.geospatial.crs import CRSManager
from app.geospatial.validation import GeospatialValidator
from app.core.exceptions import GeospatialMismatchError, UnsupportedModalityError


def test_crs_compatibility():
    assert CRSManager.are_crs_compatible("EPSG:4326", "EPSG:4326") is True
    assert CRSManager.are_crs_compatible("EPSG:3857", "EPSG:3857") is True
    assert CRSManager.are_crs_compatible(None, "EPSG:4326") is True


def test_iou_bounds():
    b1 = [0.0, 0.0, 10.0, 10.0]
    b2 = [5.0, 5.0, 15.0, 15.0]
    iou = CRSManager.compute_iou_bounds(b1, b2)
    assert 0.14 < iou < 0.15

    # Non-overlapping
    b3 = [20.0, 20.0, 30.0, 30.0]
    assert CRSManager.compute_iou_bounds(b1, b3) == 0.0


def test_bitemporal_validation_success():
    meta1 = {
        "crs": "EPSG:4326",
        "bounds": [77.0, 28.0, 77.1, 28.1],
        "width": 512,
        "height": 512,
        "resolution_x": 10.0,
        "is_georeferenced": True
    }
    meta2 = {
        "crs": "EPSG:4326",
        "bounds": [77.0, 28.0, 77.1, 28.1],
        "width": 512,
        "height": 512,
        "resolution_x": 10.0,
        "is_georeferenced": True
    }
    val = GeospatialValidator.validate_bitemporal_pair(meta1, meta2)
    assert val["valid"] is True
    assert val["crs_compatible"] is True
    assert val["dimensions_match"] is True


def test_bitemporal_spatial_mismatch():
    meta1 = {
        "crs": "EPSG:4326",
        "bounds": [77.0, 28.0, 77.1, 28.1],
        "width": 512,
        "height": 512,
        "is_georeferenced": True
    }
    meta2 = {
        "crs": "EPSG:4326",
        "bounds": [85.0, 15.0, 85.1, 15.1],  # Far away
        "width": 512,
        "height": 512,
        "is_georeferenced": True
    }
    with pytest.raises(GeospatialMismatchError):
        GeospatialValidator.validate_bitemporal_pair(meta1, meta2)
