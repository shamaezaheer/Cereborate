import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.idea import IdeaResponse


class SessionStartRequest(BaseModel):
    message: str


class SessionRespondRequest(BaseModel):
    message: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    status: str
    mode: str
    conversation_history: list[dict]
    extracted_data: dict
    idea_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCompleteResponse(BaseModel):
    session: SessionResponse
    idea: IdeaResponse
