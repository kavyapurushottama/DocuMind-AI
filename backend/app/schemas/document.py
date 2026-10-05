import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    filename: str
    file_type: str
    file_size_bytes: int = 0
    status: DocumentStatus
    status_detail: str | None = None
    error_message: str | None = None
    author: str | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None
    tags: str | None = None
    language: str | None = None
    department: str | None = None
    document_type: str | None = None
    page_count: int | None = None
    chunk_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_documents: int = 0
    total_chats: int = 0
    storage_used_bytes: int = 0
    recent_documents: list[DocumentResponse] = []
