"""
SatQuery AI - Chat API
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException

from app.schemas.chat import ChatRequest
from app.schemas.response import APIResponse
from app.services.chat_service import generate_chat_response
from app.api.dependencies import get_optional_user
from app.db.models import User


router = APIRouter(
    prefix="/chat",
    tags=["AI Chat"]
)


@router.post("")
async def chat_with_ai(
    req: ChatRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):

    request_id = getattr(
        request.state,
        "request_id",
        "unknown"
    )

    try:

        history = [
            {
                "role": item.role,
                "content": item.content
            }
            for item in req.history
        ]

        reply = await generate_chat_response(
            message=req.message,
            history=history
        )

        return APIResponse(
            success=True,
            data={
                "reply": reply
            },
            request_id=request_id
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Chat service error: {str(exc)}"
        )