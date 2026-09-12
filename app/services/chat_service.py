"""
SatQuery AI - AI Chat Service
"""

from typing import List, Dict, Any
import httpx

from app.core.config import settings


PLACEHOLDER_API_KEYS = {
    "YOUR_OPENAI_API_KEY_HERE",
    "YOUR_OPENAI_API_KEY",
    "OPENAI_API_KEY_HERE",
    "",
}


def _is_placeholder_openai_key(key: str) -> bool:
    if not key:
        return True

    normalized = key.strip().upper()
    return normalized in {item.upper() for item in PLACEHOLDER_API_KEYS} or normalized.startswith("YOUR_") or "YOUR_OPE" in normalized


def _local_satquery_reply(message: str) -> str:
    """Return a deterministic SatQuery-style answer when the OpenAI path is unavailable.

    The reply is based on the user's incoming message so different question types
    produce different remote-sensing guidance instead of repeating one canned phrase.
    """
    msg = (message or "").lower()

    if any(term in msg for term in ["ground", "bbox", "box", "object", "detect", "localize", "where is"]):
        return (
            "SatQuery AI can localize and ground visual objects in satellite imagery by "
            "returning spatial boxes, labels, and image evidence for the requested remote "
            "sensing target."
        )

    if any(term in msg for term in ["change", "compare", "before", "after", "temporal", "difference"]):
        return (
            "SatQuery AI can compare two satellite scenes over time and detect land-cover, "
            "structure, and pixel-level changes by following a bi-temporal change detection "
            "workflow."
        )

    if any(term in msg for term in ["sar", "fusion", "radar", "optical", "combine", "multimodal"]):
        return (
            "SatQuery AI can fuse optical and SAR evidence to explain terrain visibility, "
            "surface geometry, and radar backscatter for a more robust remote sensing answer."
        )

    if any(term in msg for term in ["vqa", "image", "question", "what", "where", "why", "how"]):
        return (
            "SatQuery AI supports single-image VQA and question-answering over satellite "
            "imagery, land cover, infrastructure, agriculture, and geospatial context."
        )

    return (
        "SatQuery AI is running in local demo mode. I can explain remote sensing tasks such "
        "as VQA, visual grounding, change detection, and optical-SAR fusion while the "
        "OpenAI service is unavailable or has no active billing."
    )


def _fallback_reply(message: str = "") -> str:
    return _local_satquery_reply(message)


SATQUERY_SYSTEM_PROMPT = """
You are SatQuery AI, an intelligent assistant for the SatQuery AI
remote sensing and satellite imagery platform.

Your main areas of expertise are:

- Satellite imagery
- Remote sensing
- Earth observation
- Optical satellite imagery
- SAR / Synthetic Aperture Radar
- Multispectral imagery
- Hyperspectral imagery
- Change detection
- Image classification
- Visual question answering
- Object detection
- Geospatial analysis
- Optical + SAR image fusion
- Satellite image interpretation
- GIS concepts
- CRS and geospatial concepts

You are also an assistant for users working with the SatQuery AI project.

Answer questions in a simple and understandable way.

If the user asks about SatQuery AI itself, explain the project
based on the following architecture:

Natural Language Query
        ↓
Query Understanding
        ↓
Geospatial Validation
        ↓
Image Preprocessing / Registration
        ↓
Agent / Tool Selection
        ↓
Specialist Remote Sensing Models
        ↓
Evidence Generation
        ↓
Confidence Scoring
        ↓
Final Explainable Answer

The project supports concepts such as:

- Remote sensing VQA
- Visual grounding
- Temporal change detection
- Optical-SAR fusion
- Evidence generation
- Confidence scoring
- Explainable AI

Important rules:

1. Do not invent satellite data.
2. Do not claim that an image was analyzed unless image analysis
   was actually performed.
3. Clearly say when something is a general explanation.
4. Keep answers concise unless the user asks for detail.
5. Use examples when they help.
6. Prefer simple language suitable for students and project
   presentations.
7. When explaining technical concepts, give a short definition
   first and then explain how it relates to SatQuery AI.
"""


def _is_placeholder_openai_key(key: str) -> bool:
    if not key:
        return True

    normalized = key.strip().upper()
    return normalized in {
        item.upper() for item in PLACEHOLDER_API_KEYS
    } or normalized.startswith("YOUR_") or "YOUR_OPE" in normalized


async def generate_chat_response(
    message: str,
    history: List[Dict[str, Any]]
) -> str:

    if not settings.OPENAI_API_KEY or _is_placeholder_openai_key(settings.OPENAI_API_KEY):
        return _fallback_reply(message)

    # Keep only the latest 20 messages
    history = history[-20:]

    conversation = []

    for item in history:
        role = item.get("role")

        if role not in ("user", "assistant"):
            continue

        content = item.get("content", "")

        if not content:
            continue

        conversation.append(
            {
                "role": role,
                "content": content
            }
        )

    # Add current user message
    conversation.append(
        {
            "role": "user",
            "content": message
        }
    )

    payload = {
        "model": settings.OPENAI_MODEL,
        "instructions": SATQUERY_SYSTEM_PROMPT,
        "input": conversation,
    }

    base_url = settings.OPENAI_BASE_URL.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prefer a generic OpenAI-compatible chat/completions endpoint when the
    # configured base URL is not the default OpenAI responses endpoint.
    # This allows the same backend code to target local or alternate providers.
    use_chat_completions = not base_url.startswith("https://api.openai.com")

    try:

        async with httpx.AsyncClient(timeout=60.0) as client:
            if use_chat_completions:
                payload = {
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": SATQUERY_SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ],
                }
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {}
                    error_message = error_data.get("error", {}).get("message") or f"HTTP {response.status_code}"
                    return _fallback_reply(message)

                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    message_obj = choices[0].get("message", {})
                    reply = message_obj.get("content")
                    if isinstance(reply, list):
                        reply = "\n".join(item.get("text", "") for item in reply if isinstance(item, dict))
                    if reply:
                        return reply.strip()
                return "I received a response from the AI service, but no text response was available."

            else:
                payload = {
                    "model": settings.OPENAI_MODEL,
                    "instructions": SATQUERY_SYSTEM_PROMPT,
                    "input": conversation,
                }
                response = await client.post(
                    f"{base_url}/responses",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:

                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {}

                    error_message = (
                        error_data
                        .get("error", {})
                        .get("message")
                    ) or f"OpenAI API error: HTTP {response.status_code}"

                    return _fallback_reply(message)

                data = response.json()

                reply = data.get("output_text")
                if reply:
                    return reply.strip()

                output = data.get("output", [])
                text_parts = []

                for item in output:
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            text = content.get("text", "")
                            if text:
                                text_parts.append(text)

                reply = "\n".join(text_parts).strip()
                if reply:
                    return reply

                return (
                    "I received a response from the AI service, "
                    "but no text response was available."
                )

    except httpx.TimeoutException:
        return _fallback_reply(message)

    except httpx.RequestError as exc:
        return _fallback_reply(message)

    except RuntimeError:
        return _fallback_reply(message)