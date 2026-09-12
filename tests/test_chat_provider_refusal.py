import pytest

from app.core.config import settings
from app.services.chat_service import generate_chat_response


@pytest.mark.asyncio
async def test_generate_chat_response_handles_provider_refusal_gracefully(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-valid-looking")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    class FakeResponse:
        status_code = 402

        def json(self):
            return {
                "error": {
                    "message": "You have no credits remaining. Add credits to continue using the API."
                }
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.chat_service.httpx.AsyncClient", lambda timeout=60.0: FakeClient())

    reply = await generate_chat_response("hello", [])

    assert "SatQuery AI is running in local demo mode" in reply
    assert "billing" in reply.lower()
