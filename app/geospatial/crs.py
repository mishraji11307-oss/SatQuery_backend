"""
SatQuery AI - Coordinate Reference System (CRS) & Projection Utilities
"""
from typing import Optional, List, Tuple, Dict, Any
from app.core.logging import logger

try:
    from pyproj import CRS as PyprojCRS, Transformer
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


class CRSManager:
    @staticmethod
    def are_crs_compatible(crs1: Optional[str], crs2: Optional[str]) -> bool:
        """Determines if two CRS strings represent the same coordinate space."""
        if not crs1 or not crs2:
            return True  # Lenient fallback if one lacks georeference

        c1 = crs1.strip().upper()
        c2 = crs2.strip().upper()

        if c1 == c2:
            return True

        if _HAS_PYPROJ:
            try:
                p1 = PyprojCRS.from_user_input(c1)
                p2 = PyprojCRS.from_user_input(c2)
                return p1.to_epsg() == p2.to_epsg() if p1.to_epsg() and p2.to_epsg() else p1 == p2
            except Exception as e:
                logger.warning(f"CRS parsing check warning: {e}")

        # Basic string matching for standard EPSG codes
        if "4326" in c1 and "4326" in c2:
            return True
        if "3857" in c1 and "3857" in c2:
            return True

        return False

    @staticmethod
    def compute_iou_bounds(b1: List[float], b2: List[float]) -> float:
        """
        Computes Intersection over Union of two bounding boxes [minx, miny, maxx, maxy].
        """
        if not b1 or not b2 or len(b1) != 4 or len(b2) != 4:
            return 1.0

        ix_min = max(b1[0], b2[0])
        iy_min = max(b1[1], b2[1])
        ix_max = min(b1[2], b2[2])
        iy_max = min(b1[3], b2[3])

        iw = max(0.0, ix_max - ix_min)
        ih = max(0.0, iy_max - iy_min)
        inter_area = iw * ih

        area1 = max(0.0, b1[2] - b1[0]) * max(0.0, b1[3] - b1[1])
        area2 = max(0.0, b2[2] - b2[0]) * max(0.0, b2[3] - b2[1])
        union_area = area1 + area2 - inter_area

        if union_area <= 0:
            return 0.0
        return float(inter_area / union_area)
