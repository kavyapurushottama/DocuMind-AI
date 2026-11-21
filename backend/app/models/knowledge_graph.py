import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentEntity(Base):
    """Stores extracted knowledge graph entities persisted in PostgreSQL."""
    __tablename__ = "document_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    entity_key = Column(String(255), nullable=False, index=True)  # Normalized key (e.g. "postgresql")
    label = Column(String(255), nullable=False)                   # Human-readable label (e.g. "PostgreSQL")
    category = Column(String(100), default="Concept")
    description = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="entities")


class DocumentRelationship(Base):
    """Stores directed relationships between knowledge graph entities persisted in PostgreSQL."""
    __tablename__ = "document_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_key = Column(String(255), nullable=False, index=True)  # source entity key
    target_key = Column(String(255), nullable=False, index=True)  # target entity key
    relation = Column(String(255), nullable=False)                # verb / predicate
    confidence = Column(Float, default=1.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="relationships")

