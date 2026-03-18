"""WebSocket handler for real-time planning chat with streaming LLM tokens."""

import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.llm.client import get_llm_client
from app.models.user import TenantMembership
from app.services.planning_service import PlanningService

router = APIRouter()


async def _authenticate_ws(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


@router.websocket("/ws/plan/{session_id}")
async def planning_websocket(websocket: WebSocket, session_id: uuid.UUID):
    # Auth via query param (standard for WS)
    token = websocket.query_params.get("token")
    user_id = await _authenticate_ws(token or "")

    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    async with AsyncSessionLocal() as db:
        svc = PlanningService(db, get_llm_client())
        session = await svc.get_session(session_id)

        if not session:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close(code=4004)
            return

        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)

                if data.get("type") == "message":
                    user_message = data.get("content", "")

                    # Update session and get extraction
                    updated_session, assistant_text = await svc.respond(
                        session_id, user_message
                    )

                    # Stream the response token by token (simulate for now,
                    # real streaming comes from LLM client)
                    await websocket.send_json({
                        "type": "message",
                        "content": assistant_text,
                        "extracted": updated_session.extracted_data,
                        "is_complete": updated_session.extracted_data.get("is_complete", False),
                    })

                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            pass
