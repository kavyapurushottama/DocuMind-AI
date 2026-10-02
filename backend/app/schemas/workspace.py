import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    document_count: int = 0
    chat_count: int = 0

    class Config:
        from_attributes = True
