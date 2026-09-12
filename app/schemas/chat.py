"""
SatQuery AI - Chat API Schemas
"""

from typing import List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(
        ...,
        description="Message role: user or assistant"
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000
    )


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's chat message"
    )

    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous chat messages"
    )


class ChatResponse(BaseModel):
    reply: str