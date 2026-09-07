"""
SatQuery AI - Query Planner & Router Tests
"""
import pytest
from app.agent.router import QueryRouter
from app.agent.planner import QueryPlanner
from app.core.exceptions import QueryPlanningError


def test_query_router_vqa():
    res = QueryRouter.route_query("What type of airport infrastructure is visible?", num_images=1)
    assert res["intent"] == "single_image_vqa"
    assert res["confidence"] >= 0.70


def test_query_router_grounding():
    res = QueryRouter.route_query("Where are the aircraft parked on the tarmac?", num_images=1)
    assert res["intent"] == "grounding"
    assert res["confidence"] >= 0.80


def test_query_router_temporal_change():
    res = QueryRouter.route_query("What changed between these two dates?", num_images=2)
    assert res["intent"] == "temporal_change"
    assert res["confidence"] >= 0.85


def test_query_router_optical_sar():
    res = QueryRouter.route_query(
        "Compare optical and SAR radar backscatter",
        num_images=2,
        modalities=["optical", "sar"]
    )
    assert res["intent"] == "optical_sar_analysis"
    assert res["confidence"] >= 0.85


def test_query_planner_policy_enforcement():
    planner = QueryPlanner()
    # Fails if temporal change has only 1 image
    with pytest.raises(QueryPlanningError):
        planner.create_plan(
            query="What changed?",
            uploaded_images=[{"id": "img1", "modality": "optical"}],
            force_task="temporal_change"
        )
