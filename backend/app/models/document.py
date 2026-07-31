import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt, md
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)

    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    status_detail = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
