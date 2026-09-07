"""
SatQuery AI - Confidence Service Tests
"""
from app.services.confidence_service import ConfidenceService


def test_confidence_calculation_high():
    conf = ConfidenceService.calculate_confidence(
        raw_model_conf=0.95,
        routing_conf=0.92,
        geospatial_meta={"crs_compatible": True, "dimensions_match": True},
        cross_modal_agreement="high",
        evidence_count=3
    )
    assert conf.score >= 0.85
    assert conf.level == "high"
    assert len(conf.factors) >= 4
    assert len(conf.warnings) == 0


def test_confidence_calculation_with_warnings():
    conf = ConfidenceService.calculate_confidence(
        raw_model_conf=0.60,
        routing_conf=0.60,
        geospatial_meta={"crs_compatible": False, "dimensions_match": False},
        cross_modal_agreement="low",
        evidence_count=1
    )
    assert conf.score < 0.65
    assert conf.level == "low"
    assert len(conf.warnings) > 0
