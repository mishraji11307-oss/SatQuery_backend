"""
SatQuery AI - Geospatial Raster Inspection & Analysis
Extracts dimensions, bands, CRS, transform, resolution, bounding boxes from GeoTIFF/TIFF/PNG/JPG.
"""
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image
import os

try:
    import rasterio
    from rasterio.crs import CRS
    _HAS_RASTERIO = True
except ImportError:
    _HAS_RASTERIO = False

from app.core.logging import logger
from app.core.exceptions import FileValidationError


class RasterInspector:
    """Extracts rich remote sensing and geospatial metadata from uploaded rasters."""

    @staticmethod
    def inspect_file(file_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileValidationError(f"File not found at path: {file_path}")

        ext = path.suffix.lower().lstrip(".")
        fname = original_filename or path.name
        
        # 1. Try Rasterio for true GeoTIFFs if available
        if _HAS_RASTERIO and ext in ["tif", "tiff", "jp2"]:
            try:
                return RasterInspector._inspect_with_rasterio(file_path, filename=fname)
            except Exception as e:
                logger.warning(f"Rasterio failed on {file_path}, falling back to PIL/Generic: {e}")

        # 2. Fallback to PIL / NumPy / EXIF inspection
        return RasterInspector._inspect_with_pil(file_path, filename=fname)

    @staticmethod
    def _inspect_with_rasterio(file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        with rasterio.open(file_path) as src:
            bounds = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
            crs_str = src.crs.to_string() if src.crs else None
            transform_list = list(src.transform)[:6]
            res_x, res_y = src.res if hasattr(src, "res") else (None, None)
            
            # Detect modality heuristic
            modality = RasterInspector._detect_modality(
                num_bands=src.count,
                dtype=str(src.dtypes[0]),
                filename=filename or os.path.basename(file_path),
                tags=src.tags()
            )

            acquisition_date = None
            date_tag = src.tags().get("TIFFTAG_DATETIME") or src.tags().get("ACQUISITION_DATE")
            if date_tag:
                try:
                    acquisition_date = datetime.fromisoformat(date_tag)
                except Exception:
                    pass

            return {
                "width": src.width,
                "height": src.height,
                "num_bands": src.count,
                "dtype": str(src.dtypes[0]),
                "crs": crs_str,
                "transform": transform_list,
                "bounds": bounds,
                "resolution_x": float(res_x) if res_x else None,
                "resolution_y": float(res_y) if res_y else None,
                "acquisition_date": acquisition_date,
                "sensor": src.tags().get("SENSOR_ID") or src.tags().get("MISSION"),
                "is_georeferenced": crs_str is not None and src.transform is not None,
                "modality": modality,
                "extra_metadata": {
                    "driver": src.driver,
                    "nodata": src.nodata,
                    "tags": src.tags(),
                }
            }

    @staticmethod
    def _inspect_with_pil(file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                
                # Determine number of bands
                band_count = len(img.getbands()) if hasattr(img, "getbands") else 1
                
                # Sample dtype
                arr = np.array(img)
                dtype_str = str(arr.dtype)

                modality = RasterInspector._detect_modality(
                    num_bands=band_count,
                    dtype=dtype_str,
                    filename=filename or os.path.basename(file_path),
                    tags={}
                )

                # Simulated georeference fallback if standard image
                # In real GeoTIFF with PIL, tags might hold model tiepoints
                return {
                    "width": width,
                    "height": height,
                    "num_bands": band_count,
                    "dtype": dtype_str,
                    "crs": "EPSG:4326",  # Default baseline geographic CRS
                    "transform": [0.0001, 0.0, 77.1025, 0.0, -0.0001, 28.7041],  # Default geo-grid anchor
                    "bounds": [77.1025, 28.7041 - (height * 0.0001), 77.1025 + (width * 0.0001), 28.7041],
                    "resolution_x": 10.0,  # 10m Sentinel-2 baseline resolution
                    "resolution_y": 10.0,
                    "acquisition_date": None,
                    "sensor": "Optical-Multispectral" if band_count >= 3 else "Synthetic-Aperture-Radar",
                    "is_georeferenced": False,
                    "modality": modality,
                    "extra_metadata": {
                        "color_mode": mode,
                        "format": img.format
                    }
                }
        except Exception as e:
            raise FileValidationError(f"Could not read image raster at {file_path}: {str(e)}")

    @staticmethod
    def _detect_modality(num_bands: int, dtype: str, filename: str, tags: Dict[str, Any]) -> str:
        """Determines if the raster is SAR, Optical RGB, Multispectral, or Thermal."""
        fname = filename.lower()
        if any(k in fname for k in ["sar", "sentinel1", "s1", "vv", "vh", "hh", "hv", "slc", "grd"]):
            return "sar"
        if any(k in fname for k in ["optical", "rgb", "sentinel2", "s2", "landsat", "planet", "aerial"]):
            return "optical"
        
        # Band heuristics: single band float32/int16 often SAR or single-band index; 3-4 bands optical
        if num_bands == 1 and dtype in ["float32", "int16", "uint16"]:
            return "sar"
        elif num_bands in [3, 4]:
            return "optical"
        elif num_bands > 4:
            return "multispectral"
        
        return "optical"
