import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.chat import MessageRole


class Citation(BaseModel):
    filename: str
    page: int | None = None
    chunk_id: str
    snippet: str
    score: float


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    # None = search across all of the user's documents
    document_id: uuid.UUID | None = None
    # None = start a new conversation
    conversation_id: uuid.UUID | None = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list[Citation] | None
    created_at: datetime

    class Config:
        from_attributes = True


class AskResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageResponse


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    document_id: uuid.UUID | None
    is_pinned: bool
    created_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    document_id: uuid.UUID | None
    is_pinned: bool
    created_at: datetime

    class Config:
        from_attributes = True
