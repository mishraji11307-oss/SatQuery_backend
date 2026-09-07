"""
SatQuery AI - Query Router & Intent Classifier
Classifies natural-language queries into remote sensing tasks with confidence & ambiguity handling.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from app.core.logging import logger


class QueryRouter:
    """Classifies user natural-language queries into remote-sensing intent categories."""

    INTENT_KEYWORDS = {
        "grounding": [
            r"\bwhere\b", r"\blocate\b", r"\bfind\b", r"\bpoint out\b",
            r"\bhighlight\b", r"\bbounding box\b", r"\bdetect\b", r"\bpinpoint\b",
            r"\bwhere is\b", r"\bwhere are\b", r"\bshow me the\b", r"\bpositions of\b"
        ],
        "temporal_change": [
            r"\bwhat changed\b", r"\bchange between\b", r"\btemporal\b",
            r"\bdifference between\b", r"\bhow did .* change\b", r"\bnew structures\b",
            r"\bdeforestation\b", r"\bexpansion\b", r"\bcompare images\b", r"\bbefore and after\b",
            r"\bt1.*t2\b", r"\bvariation\b", r"\bconstruction progress\b"
        ],
        "change_vqa": [
            r"\bdid .* change\b", r"\bwhy did .* change\b", r"\bhow many new .* were built\b",
            r"\bhas .* expanded\b", r"\bwas there flood\b", r"\bwhich area altered\b"
        ],
        "optical_sar_analysis": [
            r"\bsar\b", r"\bradar\b", r"\boptical and sar\b", r"\bmultimodal\b",
            r"\bcloud penetration\b", r"\bmicrowave\b", r"\bbackscatter\b",
            r"\bcompare optical and sar\b", r"\bcross-modal\b", r"\bpolarimetric\b"
        ],
        "metadata_query": [
            r"\bcrs\b", r"\bcoordinate system\b", r"\bresolution\b", r"\bdimensions\b",
            r"\bacquisition date\b", r"\bsensor type\b", r"\bhow many bands\b", r"\bprojection\b"
        ],
        "single_image_vqa": [
            r"\bwhat\b", r"\bdescribe\b", r"\bcount\b", r"\bhow many\b",
            r"\bis there\b", r"\bare there\b", r"\bwhat type of\b", r"\bexplain the scene\b",
            r"\bclassify\b", r"\bwhat is in this\b"
        ]
    }

    @classmethod
    def route_query(
        cls,
        query: str,
        num_images: int = 1,
        modalities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Routes the query based on textual keywords, image count, and detected modalities.
        Returns: {
            "intent": str,
            "confidence": float,
            "matched_keywords": List[str],
            "is_ambiguous": bool,
            "suggested_task": str
        }
        """
        q_clean = query.strip().lower()
        modalities = modalities or ["optical"]

        # Check multimodal indicators first
        has_sar = any(m == "sar" for m in modalities)
        has_optical = any(m in ["optical", "multispectral"] for m in modalities)

        intent_scores: Dict[str, float] = {}
        matched_words: Dict[str, List[str]] = {}

        for intent, patterns in cls.INTENT_KEYWORDS.items():
            matches = []
            for pat in patterns:
                found = re.findall(pat, q_clean)
                if found:
                    matches.extend(found)
            if matches:
                # Calculate heuristic score based on match count
                intent_scores[intent] = min(1.0, 0.65 + 0.15 * len(matches))
                matched_words[intent] = matches

        # Contextual boosts based on image count and modalities
        if num_images >= 2:
            if has_sar and has_optical:
                intent_scores["optical_sar_analysis"] = max(intent_scores.get("optical_sar_analysis", 0.0), 0.92)
            else:
                intent_scores["temporal_change"] = max(intent_scores.get("temporal_change", 0.0), 0.88)
        elif num_images == 1:
            # Single image cannot do temporal change
            intent_scores.pop("temporal_change", None)
            intent_scores.pop("change_vqa", None)

        if not intent_scores:
            # Fallback to single_image_vqa if 1 image, temporal_change if 2 images
            if num_images == 1:
                return {
                    "intent": "single_image_vqa",
                    "confidence": 0.75,
                    "matched_keywords": [],
                    "is_ambiguous": False,
                    "suggested_task": "single_image_vqa"
                }
            elif num_images == 2 and has_sar and has_optical:
                return {
                    "intent": "optical_sar_analysis",
                    "confidence": 0.85,
                    "matched_keywords": [],
                    "is_ambiguous": False,
                    "suggested_task": "optical_sar_analysis"
                }
            else:
                return {
                    "intent": "temporal_change",
                    "confidence": 0.80,
                    "matched_keywords": [],
                    "is_ambiguous": False,
                    "suggested_task": "temporal_change"
                }

        # Select highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]

        # Ambiguity check (if 2 intents are very close in score)
        sorted_scores = sorted(intent_scores.values(), reverse=True)
        is_ambiguous = len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1] < 0.08)

        return {
            "intent": best_intent,
            "confidence": round(confidence, 2),
            "matched_keywords": matched_words.get(best_intent, []),
            "is_ambiguous": is_ambiguous,
            "suggested_task": best_intent
        }
