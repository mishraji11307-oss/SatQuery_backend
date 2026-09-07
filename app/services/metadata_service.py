"""
SatQuery AI - Remote Sensing Metadata Extraction Service
"""
from typing import Dict, Any
from app.geospatial.raster import RasterInspector
from app.core.logging import logger


class MetadataService:
    """Service layer extracting geospatial, radiometric, and temporal attributes."""

    @staticmethod
    def extract_image_metadata(file_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """Extracts complete metadata dictionary for a stored raster."""
        meta = RasterInspector.inspect_file(file_path, original_filename=original_filename)
        logger.info(
            f"Extracted metadata for {file_path}: shape=({meta.get('height')}, {meta.get('width')}), "
            f"bands={meta.get('num_bands')}, crs={meta.get('crs')}, modality={meta.get('modality')}"
        )
        return meta
