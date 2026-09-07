"""
SatQuery AI - Evidence Management & Aggregation Service
"""
from typing import Dict, Any, List, Optional
from app.schemas.evidence import EvidenceItemSchema, BoundingBox


class EvidenceService:
    """Standardizes, aggregates and prepares visual evidence for client inspection."""

    @staticmethod
    def format_evidence_items(raw_items: List[Dict[str, Any]]) -> List[EvidenceItemSchema]:
        """Converts raw tool output dictionaries into validated EvidenceItemSchema instances."""
        formatted: List[EvidenceItemSchema] = []

        for item in raw_items:
            bboxes_data = item.get("bboxes")
            parsed_bboxes = None
            if bboxes_data:
                parsed_bboxes = [
                    BoundingBox(
                        label=b.get("label", "object"),
                        confidence=b.get("confidence", 1.0),
                        box_2d=b.get("box_2d", [0, 0, 1, 1]),
                        geo_bbox=b.get("geo_bbox")
                    )
                    for b in bboxes_data
                ]

            schema_item = EvidenceItemSchema(
                evidence_type=item.get("evidence_type", "model_output"),
                url=item.get("url"),
                file_path=item.get("file_path"),
                bbox=item.get("bbox"),
                bboxes=parsed_bboxes,
                geo_polygon=item.get("geo_polygon"),
                confidence=item.get("confidence", 1.0),
                source_tool=item.get("source_tool"),
                description=item.get("description"),
                metadata=item.get("metadata", {})
            )
            formatted.append(schema_item)

        return formatted
