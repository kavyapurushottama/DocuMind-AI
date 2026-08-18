import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db, SessionLocal
from app.models.chat import Conversation
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentResponse, DashboardStats
from app.services import vector_store
from app.services.chunking import chunk_pages
from app.services.extraction.docx_extractor import DocxExtractor
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.extraction.txt_extractor import TxtExtractor
from app.services import embedding_service

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
    extract -> clean (done inside extractors) -> chunk -> embed -> store.
    Only the extraction step is format-specific; everything after this
    point is identical regardless of file type.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        doc.status_detail = "Extracting text contents..."
        db.commit()

        extractor = EXTRACTORS[doc.file_type]
        pages = extractor.extract(doc.file_path)

        if not pages:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            doc.error_message = "No extractable text found in this file."
            db.commit()
            return

        doc.status_detail = "Generating sliding window text chunks..."
        db.commit()

        chunks = chunk_pages(pages)
        if not chunks:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            doc.error_message = "Text was extracted but no chunks could be built."
            db.commit()
            return

        doc.status_detail = f"Vectorizing {len(chunks)} text chunks..."
        db.commit()

        vectors = embedding_service.embed_texts([c.text for c in chunks])

        doc.status_detail = "Storing vector index in Qdrant store..."
        db.commit()

        vector_store.upsert_chunks(
            document_id=str(doc.id),
            user_id=str(doc.user_id),
            filename=doc.filename,
            chunk_texts=[c.text for c in chunks],
            chunk_pages=[c.page_number for c in chunks],
            chunk_indices=[c.chunk_index for c in chunks],
            vectors=vectors,
        )

        doc.page_count = len(pages)
        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.READY
        doc.status_detail = None
        db.commit()
    except Exception as e:  # noqa: BLE001 - surface any failure back to the user
        db.rollback()
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = None
            doc.error_message = str(e)[:500]
            db.commit()
    finally:
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

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    doc_id = uuid.uuid4()
    stored_name = f"{doc_id}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        file_path=file_path,
        file_size_bytes=len(contents),
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Dispatch ingestion to background task so HTTP upload response returns instantly (< 0.1s)
    background_tasks.add_task(process_document, str(doc.id))

    return doc


def _auto_cleanup_stuck_documents(db: Session, user_id: uuid.UUID) -> None:
    """Auto-recovers any document frozen in processing state from an old server build/deploy."""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=3)
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
            doc.error_message = "Ingestion timed out on previous server build. Please delete and re-upload."
        db.commit()


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
    storage_used = sum(d.file_size_bytes for d in docs)
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


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import logging
    logger = logging.getLogger(__name__)
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        vector_store.delete_document_chunks(str(doc.id))
    except Exception as e:
        logger.warning(f"Failed to delete Qdrant chunks for document {document_id}: {e}")

    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Failed to remove file from disk: {e}")

    db.delete(doc)
    db.commit()


@router.get("/{document_id}/download")
def download_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import mimetypes
    from fastapi.responses import FileResponse
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File on disk not found")
    
    media_type, _ = mimetypes.guess_type(doc.filename)
    if not media_type:
        media_type = "application/octet-stream"
        
    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=media_type,
        content_disposition_type="inline"
    )
