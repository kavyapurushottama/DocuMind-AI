import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.chat import Conversation
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = Workspace(user_id=current_user.id, name=data.name.strip())
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        created_at=ws.created_at,
        document_count=0,
        chat_count=0,
    )


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = (
        db.query(Workspace)
        .filter(Workspace.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )
    res = []
    for ws in workspaces:
        doc_count = db.query(Document).filter(Document.workspace_id == ws.id).count()
        chat_count = db.query(Conversation).filter(Conversation.workspace_id == ws.id).count()
        res.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                created_at=ws.created_at,
                document_count=doc_count,
                chat_count=chat_count,
            )
        )
    return res


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    doc_count = db.query(Document).filter(Document.workspace_id == ws.id).count()
    chat_count = db.query(Conversation).filter(Conversation.workspace_id == ws.id).count()
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        created_at=ws.created_at,
        document_count=doc_count,
        chat_count=chat_count,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    db.delete(ws)
    db.commit()


@router.post("/{workspace_id}/assign-document/{document_id}")
def assign_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.workspace_id = ws.id
    db.commit()
    return {"status": "ok", "workspace_id": str(ws.id), "document_id": str(doc.id)}
