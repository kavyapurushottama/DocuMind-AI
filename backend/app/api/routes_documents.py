import logging
import mimetypes
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db, SessionLocal
from app.models.chat import Conversation
from app.models.document import Document, DocumentStatus, DocumentFile
from app.models.user import User
from app.schemas.document import DocumentResponse, DashboardStats
from app.services import vector_store, embedding_service
from app.services.chunking import chunk_pages
from app.services.extraction.docx_extractor import DocxExtractor
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.extraction.txt_extractor import TxtExtractor
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

EXTRACTORS = {
    "pdf": PdfExtractor(),
    "docx": DocxExtractor(),
    "txt": TxtExtractor(),
    "md": TxtExtractor(),
}


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def process_document(document_id: str) -> None:
    """
    The universal ingestion pipeline, run as a background task:
    extract -> clean -> chunk -> embed -> store.
    """
    db = SessionLocal()
    storage = get_storage_service()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        doc.status_detail = "Extracting text contents..."
        db.commit()

        import gc

        # Re-materialize file from persistent database storage if wiped from local disk
        if not storage.exists(doc.file_path):
            doc_file = db.query(DocumentFile).filter(DocumentFile.document_id == doc.id).first()
            if doc_file and doc_file.file_data:
                doc.file_path = storage.save(str(doc.id), doc.file_type, doc_file.file_data)
                db.commit()
            else:
                doc.status = DocumentStatus.FAILED
                doc.status_detail = None
                doc.error_message = "Source file not found on storage."
                db.commit()
                return

        extractor = EXTRACTORS[doc.file_type]
        pages = extractor.extract(doc.file_path)
        gc.collect()

        if not pages:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            doc.error_message = "No extractable text found in this file."
            db.commit()
            return

        doc.status_detail = "Generating sliding window text chunks..."
        db.commit()

        chunks = chunk_pages(pages)
        gc.collect()
        if not chunks:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            doc.error_message = "Text was extracted but no chunks could be built."
            db.commit()
            return

        # Extract and persist Knowledge Graph triples for multi-hop relational reasoning
        try:
            from app.services.knowledge_graph import extract_entities_and_relations, get_user_graph
            from app.models.knowledge_graph import DocumentEntity, DocumentRelationship
            sample_text = " ".join([c.text for c in chunks[:4]])
            kg_data = extract_entities_and_relations(sample_text)

            # Clean any previously extracted entities for this document
            db.query(DocumentEntity).filter(DocumentEntity.document_id == doc.id).delete()
            db.query(DocumentRelationship).filter(DocumentRelationship.document_id == doc.id).delete()

            for entity in kg_data.entities:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    entity_key=entity.id.lower().strip(),
                    label=entity.label.strip(),
                    category=entity.category,
                    description=entity.description,
                ))

            for rel in kg_data.relationships:
                db.add(DocumentRelationship(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    source_key=rel.source.lower().strip(),
                    target_key=rel.target.lower().strip(),
                    relation=rel.relation.strip(),
                    confidence=rel.confidence,
                ))

            db.commit()
            from app.services.knowledge_graph import invalidate_user_graph_cache
            invalidate_user_graph_cache(str(doc.user_id))
            user_kg = get_user_graph(str(doc.user_id), db=db)
        except Exception as kg_err:
            logger.warning("Knowledge Graph extraction/persistence notice: %s", kg_err)

        doc.status_detail = f"Vectorizing {len(chunks)} text chunks..."
        db.commit()

        import time

        # Micro-batch embedding generation (8 chunks per batch) with CPU yielding
        BATCH_SIZE = 8
        chunk_texts = [c.text for c in chunks]
        vectors = []
        for i in range(0, len(chunk_texts), BATCH_SIZE):
            batch = chunk_texts[i : i + BATCH_SIZE]
            batch_vecs = embedding_service.embed_texts(batch)
            vectors.extend(batch_vecs)
            time.sleep(0.05)
            gc.collect()

        doc.status_detail = "Storing vector index in Qdrant store..."
        db.commit()

        try:
            vector_store.delete_document_chunks(
                str(doc.id),
                str(doc.user_id),
            )
        except Exception as e:
            logger.exception(
                "Failed to clean existing vectors before reindexing document %s",
                doc.id,
            )
            raise RuntimeError(
                f"Could not prepare document {doc.id} for reindexing"
            ) from e

        vector_store.upsert_chunks(
            document_id=str(doc.id),
            user_id=str(doc.user_id),
            filename=doc.filename,
            chunk_texts=[c.text for c in chunks],
            chunk_pages=[c.page_number for c in chunks],
            chunk_indices=[c.chunk_index for c in chunks],
            vectors=vectors,
        )
        gc.collect()

        doc.page_count = len(pages)
        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.READY
        doc.status_detail = None
        doc.error_message = None
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("Ingestion failed for document %s: %s", document_id, e)
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            # Sanitize error message returned to user
            doc.error_message = "Document processing failed during ingestion. Please verify file format or retry."
            db.commit()
    finally:
        import gc
        gc.collect()
        db.close()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = _extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit.",
        )

    # Tenant storage safeguard: limit each user to 50MB total stored documents
    from sqlalchemy import func, text
    from app.database import engine
    if engine.dialect.name == "postgresql":
        try:
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:uid))"),
                {"uid": str(current_user.id)},
            )
        except Exception as e:
            logger.exception(
                "Failed to acquire storage quota lock for user %s",
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify storage quota. Please retry.",
            ) from e

    total_user_bytes = (
        db.query(func.coalesce(func.sum(Document.file_size_bytes), 0))
        .filter(Document.user_id == current_user.id)
        .scalar()
    )
    if total_user_bytes + len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage quota exceeded (50MB maximum per account). Please delete unused documents to free space.",
        )

    storage = get_storage_service()
    doc_id = uuid.uuid4()
    file_path = storage.save(str(doc_id), ext, contents)

    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        file_path=file_path,
        file_size_bytes=len(contents),
        status=DocumentStatus.PENDING,
        status_detail="Uploaded. Queued for ingestion.",
    )
    doc_file = DocumentFile(
        document_id=doc_id,
        file_data=contents,
    )
    db.add(doc)
    db.add(doc_file)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, str(doc.id))
    return doc


def _auto_cleanup_stuck_documents(db: Session, user_id: uuid.UUID) -> None:
    """Auto-recovers any document frozen in processing state from an old server build/deploy."""
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        stuck_docs = (
            db.query(Document)
            .filter(
                Document.user_id == user_id,
                Document.status.in_([DocumentStatus.PROCESSING, DocumentStatus.PENDING]),
                Document.created_at < cutoff,
            )
            .all()
        )
        if stuck_docs:
            for doc in stuck_docs:
                doc.status = DocumentStatus.FAILED
                doc.status_detail = None
                doc.error_message = "Ingestion timed out on previous server build. Please retry processing."
            db.commit()
    except Exception as e:
        logger.warning("Auto cleanup stuck documents failed: %s", e)
        db.rollback()


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _auto_cleanup_stuck_documents(db, current_user.id)
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _auto_cleanup_stuck_documents(db, current_user.id)
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    total_chats = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    storage_used = sum((d.file_size_bytes or 0) for d in docs)
    return DashboardStats(
        total_documents=len(docs),
        total_chats=total_chats,
        storage_used_bytes=storage_used,
        recent_documents=docs[:5],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/{document_id}/retry", response_model=DocumentResponse)
def retry_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows user to retry failed or stalled document ingestion."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_storage_service()
    if not storage.exists(doc.file_path):
        # Restore from persistent database storage
        doc_file = db.query(DocumentFile).filter(DocumentFile.document_id == doc.id).first()
        if doc_file and doc_file.file_data:
            doc.file_path = storage.save(str(doc.id), doc.file_type, doc_file.file_data)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source document file is no longer available. Please upload again.",
            )

    # Clean up previous Qdrant vectors to prevent duplicates on retry
    try:
        vector_store.delete_document_chunks(str(doc.id), str(current_user.id))
    except Exception as e:
        logger.warning("Notice during retry vector cleanup for document %s: %s", doc.id, e)

    doc.status = DocumentStatus.PENDING
    doc.status_detail = "Queued for retry..."
    doc.error_message = None
    db.commit()
    db.refresh(doc)
    from app.services.knowledge_graph import invalidate_user_graph_cache
    invalidate_user_graph_cache(str(current_user.id))

    background_tasks.add_task(process_document, str(doc.id))
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Detach or nullify conversations referencing this document
    from app.models.chat import Conversation
    db.query(Conversation).filter(Conversation.document_id == doc.id).update(
        {Conversation.document_id: None},
        synchronize_session=False,
    )

    # 2. Delete vectors from Qdrant with resilient fallback
    try:
        vector_store.delete_document_chunks(
            str(doc.id),
            str(current_user.id),
        )
    except Exception as e:
        logger.warning(
            "Notice: failed to delete Qdrant chunks for document %s (continuing database cleanup): %s",
            document_id,
            e,
        )

    # 3. Clean up physical file if it exists
    storage = get_storage_service()
    if doc.file_path and storage.exists(doc.file_path):
        try:
            storage.delete(doc.file_path)
        except Exception as e:
            logger.warning("Failed to delete local disk file %s: %s", doc.file_path, e)

    # 4. Delete document record (cascades to DocumentFile, DocumentEntity, DocumentRelationship)
    db.delete(doc)
    db.commit()

    from app.services.knowledge_graph import invalidate_user_graph_cache
    invalidate_user_graph_cache(str(current_user.id))


@router.get("/{document_id}/download")
def download_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    media_type, _ = mimetypes.guess_type(doc.filename)
    resolved_media_type = media_type or "application/octet-stream"

    storage = get_storage_service()
    if storage.exists(doc.file_path):
        return FileResponse(
            path=doc.file_path,
            filename=doc.filename,
            media_type=resolved_media_type,
            content_disposition_type="inline",
        )

    # Reconstruct from persistent database storage if local disk was wiped by container restart
    doc_file = db.query(DocumentFile).filter(DocumentFile.document_id == doc.id).first()
    if doc_file and doc_file.file_data:
        # Cache to local disk for future fast access
        try:
            doc.file_path = storage.save(str(doc.id), doc.file_type, doc_file.file_data)
            db.commit()
        except Exception:
            pass

        return Response(
            content=doc_file.file_data,
            media_type=resolved_media_type,
            headers={
                "Content-Disposition": f'inline; filename="{doc.filename}"'
            },
        )

    raise HTTPException(status_code=404, detail="File content not found in storage")
