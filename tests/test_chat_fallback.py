import pytest

from app.core.config import settings
from app.services.chat_service import generate_chat_response


@pytest.mark.asyncio
async def test_generate_chat_response_falls_back_when_openai_key_is_placeholder(monkeypatch):
    # Simulate the repository's default placeholder in .env
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-5.6-luna")

    reply = await generate_chat_response("hello", [])

    assert "SatQuery AI" in reply
    assert "satellite" in reply.lower()
