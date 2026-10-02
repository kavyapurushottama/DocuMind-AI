import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.guardrails import validate_and_sanitize_input
from app.database import get_db, SessionLocal
from app.models.chat import Conversation, Message, MessageRole
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.chat import AskRequest, AskResponse, ConversationResponse, ConversationSummary, MessageResponse
from app.services.rag_service import answer_question, stream_answer_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(data: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validate and sanitize input with guardrails
    sanitized_question, guardrail_error = validate_and_sanitize_input(data.question)
    if guardrail_error:
        raise HTTPException(status_code=400, detail=guardrail_error)

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
        title = sanitized_question[:60] + ("..." if len(sanitized_question) > 60 else "")
        conversation = Conversation(user_id=current_user.id, document_id=data.document_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Fetch past conversation messages BEFORE adding current question to history
    past_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    chat_history = [{"role": m.role.value, "content": m.content} for m in past_messages]

    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=sanitized_question)
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
            question=sanitized_question,
            user_id=str(current_user.id),
            document_id=str(data.document_id) if data.document_id else None,
            has_documents=has_docs,
            chat_history=chat_history,
        )
    except Exception as e:
        logger.exception(f"Error while processing chat request for user {current_user.id}: {e}")
        answer_text = "I encountered an issue processing your request. Please try asking again or upload a new document."
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


@router.post("/ask/stream")
def ask_stream(data: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Server-Sent Events (SSE) streaming endpoint for token-by-token live answer rendering."""
    sanitized_question, guardrail_error = validate_and_sanitize_input(data.question)
    if guardrail_error:
        raise HTTPException(status_code=400, detail=guardrail_error)

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
        title = sanitized_question[:60] + ("..." if len(sanitized_question) > 60 else "")
        conversation = Conversation(user_id=current_user.id, document_id=data.document_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    past_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    chat_history = [{"role": m.role.value, "content": m.content} for m in past_messages]

    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=sanitized_question)
    db.add(user_message)
    db.commit()

    has_docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.status == DocumentStatus.READY)
        .count()
        > 0
    )

    citations, token_generator = stream_answer_question(
        question=sanitized_question,
        user_id=str(current_user.id),
        document_id=str(data.document_id) if data.document_id else None,
        has_documents=has_docs,
        chat_history=chat_history,
    )

    conv_id_str = str(conversation.id)
    citations_json = [c.model_dump() for c in citations] if citations else []

    def event_generator():
        yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conv_id_str})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations_json})}\n\n"

        full_answer = ""
        try:
            for token in token_generator:
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            logger.exception(f"Error during streaming tokens: {e}")

        # Save assistant message to PostgreSQL database upon completion
        db_stream = SessionLocal()
        try:
            assistant_msg = Message(
                conversation_id=uuid.UUID(conv_id_str),
                role=MessageRole.ASSISTANT,
                content=full_answer if full_answer else "I could not generate an answer.",
                citations=citations_json,
            )
            db_stream.add(assistant_msg)
            db_stream.commit()
        finally:
            db_stream.close()

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )



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
