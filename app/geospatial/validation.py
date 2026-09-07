"""
SatQuery AI - Geospatial & Multimodal Compatibility Validation Layer
Enforces strict spatial, temporal, and spectral integrity before specialist tool invocation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.geospatial.crs import CRSManager
from app.core.exceptions import GeospatialMismatchError, UnsupportedModalityError
from app.core.logging import logger


class GeospatialValidator:
    """Validates compatibility between two or more remote sensing imagery inputs."""

    @staticmethod
    def validate_bitemporal_pair(
        meta1: Dict[str, Any],
        meta2: Dict[str, Any],
        allow_different_dimensions: bool = True
    ) -> Dict[str, Any]:
        """
        Validates T1 and T2 pair for temporal change detection.
        Checks: CRS equivalence, spatial footprint overlap, resolution proximity, temporal ordering.
        """
        # 1. CRS Check
        crs1 = meta1.get("crs")
        crs2 = meta2.get("crs")
        if not CRSManager.are_crs_compatible(crs1, crs2):
            raise GeospatialMismatchError(
                message=f"CRS Mismatch: T1 is '{crs1}' while T2 is '{crs2}'. Reprojection required.",
                details={"error_code": "CRS_MISMATCH", "t1_crs": crs1, "t2_crs": crs2}
            )

        # 2. Spatial Overlap (IoU)
        bounds1 = meta1.get("bounds")
        bounds2 = meta2.get("bounds")
        if bounds1 and bounds2:
            iou = CRSManager.compute_iou_bounds(bounds1, bounds2)
            if iou < 0.1 and meta1.get("is_georeferenced") and meta2.get("is_georeferenced"):
                raise GeospatialMismatchError(
                    message="The two temporal images do not overlap spatially (IoU < 0.10).",
                    details={"error_code": "SPATIAL_MISMATCH", "overlap_iou": round(iou, 3)}
                )

        # 3. Resolution Compatibility
        res1 = meta1.get("resolution_x")
        res2 = meta2.get("resolution_x")
        res_ratio = 1.0
        if res1 and res2 and res1 > 0 and res2 > 0:
            res_ratio = max(res1, res2) / min(res1, res2)
            if res_ratio > 5.0:
                logger.warning(f"Large resolution difference between T1 ({res1}m) and T2 ({res2}m).")

        # 4. Dimension & Grid Check
        w1, h1 = meta1.get("width", 0), meta1.get("height", 0)
        w2, h2 = meta2.get("width", 0), meta2.get("height", 0)
        dimensions_match = (w1 == w2 and h1 == h2)

        # 5. Temporal Ordering Check
        date1 = meta1.get("acquisition_date")
        date2 = meta2.get("acquisition_date")
        temporal_valid = True
        if date1 and date2 and isinstance(date1, datetime) and isinstance(date2, datetime):
            temporal_valid = (date2 >= date1)

        return {
            "valid": True,
            "crs_compatible": True,
            "dimensions_match": dimensions_match,
            "requires_resizing": not dimensions_match,
            "requires_registration": True,  # Recommended best practice before bi-temporal differencing
            "resolution_ratio": round(res_ratio, 2),
            "temporal_ordered": temporal_valid,
            "t1_shape": [h1, w1],
            "t2_shape": [h2, w2]
        }

    @staticmethod
    def validate_optical_sar_pair(
        optical_meta: Dict[str, Any],
        sar_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates an Optical and SAR image pair for multimodal fusion.
        Checks that one is optical/multispectral and one is SAR/radar.
        """
        opt_mod = optical_meta.get("modality", "optical").lower()
        sar_mod = sar_meta.get("modality", "sar").lower()

        # Check modalities
        if opt_mod not in ["optical", "multispectral", "unknown"]:
            raise UnsupportedModalityError(
                message=f"Primary input expected to be optical, but detected '{opt_mod}'",
                details={"error_code": "MODALITY_MISMATCH", "expected": "optical", "actual": opt_mod}
            )

        if sar_mod not in ["sar", "radar", "unknown"]:
            logger.warning(f"Secondary input has modality '{sar_mod}', proceeding with multimodal alignment.")

        # Spatial check
        crs1 = optical_meta.get("crs")
        crs2 = sar_meta.get("crs")
        if not CRSManager.are_crs_compatible(crs1, crs2):
            raise GeospatialMismatchError(
                message="Optical and SAR rasters have conflicting Coordinate Reference Systems.",
                details={"error_code": "CRS_MISMATCH", "optical_crs": crs1, "sar_crs": crs2}
            )

        w1, h1 = optical_meta.get("width", 0), optical_meta.get("height", 0)
        w2, h2 = sar_meta.get("width", 0), sar_meta.get("height", 0)

        return {
            "valid": True,
            "optical_modality": opt_mod,
            "sar_modality": sar_mod,
            "dimensions_match": (w1 == w2 and h1 == h2),
            "requires_coregistration": True,
            "requires_speckle_filtering": True,
            "optical_shape": [h1, w1],
            "sar_shape": [h2, w2]
        }
