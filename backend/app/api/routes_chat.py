import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.chat import Conversation, Message, MessageRole
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, ConversationResponse, ConversationSummary, MessageResponse
from app.services.rag_service import answer_question

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(data: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.document_id:
        doc = db.query(Document).filter(Document.id == data.document_id, Document.user_id == current_user.id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

    if data.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == data.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = data.question[:60] + ("..." if len(data.question) > 60 else "")
        conversation = Conversation(user_id=current_user.id, document_id=data.document_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=data.question)
    db.add(user_message)
    db.commit()

    has_docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.status == DocumentStatus.READY)
        .count()
        > 0
    )

    try:
        answer_text, citations = answer_question(
            question=data.question,
            user_id=str(current_user.id),
            document_id=str(data.document_id) if data.document_id else None,
            has_documents=has_docs,
        )
    except Exception as e:
        answer_text = f"An error occurred while processing your request: {e}"
        citations = []

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=answer_text,
        citations=[c.model_dump() for c in citations] if citations else [],
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return AskResponse(conversation_id=conversation.id, message=assistant_message)


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.is_pinned.desc(), Conversation.created_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()


@router.post("/conversations/{conversation_id}/pin")
def pin_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.is_pinned = not conversation.is_pinned
    db.commit()
    db.refresh(conversation)
    return {"is_pinned": conversation.is_pinned}
