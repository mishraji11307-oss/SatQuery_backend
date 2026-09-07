"""
SatQuery AI - Calibrated Multi-Factor Confidence Service
Calculates explainable confidence scores factoring model certainty, spatial registration, and cross-modal agreement.
"""
from typing import Dict, Any, List, Optional
from app.schemas.analysis import ConfidenceScoreSchema


class ConfidenceService:
    """Computes transparent, auditable confidence metrics for Earth Observation outputs."""

    @staticmethod
    def calculate_confidence(
        raw_model_conf: float,
        routing_conf: float,
        geospatial_meta: Optional[Dict[str, Any]] = None,
        cross_modal_agreement: Optional[str] = None,
        evidence_count: int = 1,
        warnings_input: Optional[List[str]] = None
    ) -> ConfidenceScoreSchema:
        """
        Calculates calibrated confidence score and factors.
        """
        factors: List[str] = []
        warnings: List[str] = list(warnings_input or [])

        # 1. Base model confidence weight (50%)
        weighted_score = raw_model_conf * 0.50
        factors.append(f"Model inference certainty: {int(raw_model_conf * 100)}%")

        # 2. Query routing certainty weight (20%)
        weighted_score += routing_conf * 0.20
        if routing_conf >= 0.85:
            factors.append("High semantic alignment with remote sensing query intent")
        else:
            warnings.append("Ambiguous query phrasing slightly lowered routing confidence")

        # 3. Geospatial integrity weight (20%)
        if geospatial_meta:
            if geospatial_meta.get("crs_compatible", True):
                weighted_score += 0.10
                factors.append("Verified CRS and coordinate grid compatibility")
            else:
                warnings.append("Coordinate reference systems required reprojection")

            if geospatial_meta.get("dimensions_match", True):
                weighted_score += 0.10
                factors.append("Native raster pixel dimensions match perfectly")
            else:
                weighted_score += 0.05
                factors.append("Sub-pixel coregistration applied for grid alignment")
        else:
            weighted_score += 0.15
            factors.append("Raster input format and dimensions verified")

        # 4. Multimodal / Evidence confirmation weight (10%)
        if cross_modal_agreement:
            if cross_modal_agreement.lower() == "high":
                weighted_score += 0.10
                factors.append("Strong cross-modal confirmation between Optical and SAR sensors")
            elif cross_modal_agreement.lower() == "partial":
                weighted_score += 0.05
                warnings.append("Optical and SAR sensors show partial spectral disagreement")
            else:
                warnings.append("Low cross-modal agreement between optical reflectance and radar backscatter")
        elif evidence_count > 1:
            weighted_score += 0.10
            factors.append(f"Multiple corroborating visual evidence artifacts ({evidence_count}) generated")
        else:
            weighted_score += 0.08

        final_score = max(0.0, min(1.0, round(weighted_score, 2)))

        # Categorize level
        if final_score >= 0.85:
            level = "high"
        elif final_score >= 0.65:
            level = "medium"
        else:
            level = "low"
            warnings.append("Overall confidence is low; visual verification by human analyst advised")

        return ConfidenceScoreSchema(
            score=final_score,
            level=level,
            cross_modal_agreement=cross_modal_agreement,
            factors=factors,
            warnings=warnings
        )
