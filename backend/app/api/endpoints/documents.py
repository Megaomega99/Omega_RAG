from typing import Any, List
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services.document_service import create_document, get_document_by_id, get_user_documents, update_document

#from worker.tasks.document_processing import process_document
from celery import Celery

# Initialize Celery client with broker URL
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('tasks', broker=redis_url)
router = APIRouter()


@router.get("/", response_model=List[DocumentResponse])
def read_documents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve user's documents.
    """
    documents = get_user_documents(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return documents


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    *,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload a new document.
    """
    # Check file type
    allowed_extensions = [".pdf", ".txt", ".md", ".docx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}",
        )
    
    # Create document object
    document_in = DocumentCreate(
        title=title,
        description=description
    )
    
    # Save file to disk
    from app.core.config import settings
    file_storage_path = settings.FILE_STORAGE_PATH
    
    # Create directory if it doesn't exist
    os.makedirs(file_storage_path, exist_ok=True)
    
    # Generate unique filename
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(file_storage_path, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document in database
    document = create_document(
        db=db, 
        document_in=document_in, 
        user_id=current_user.id,
        file_path=unique_filename,
        file_type=file_ext.replace(".", ""),
        original_filename=file.filename
    )
    
    # Start document processing task asynchronously
    celery_app.send_task('process_document', args=[document.id])
    
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
def read_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get document by ID.
    """
    document = get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document_endpoint(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    document_in: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update document.
    """
    document = get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
        
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    document = update_document(db=db, db_document=document, document_in=document_in)
    return document


@router.delete("/{document_id}", response_model=DocumentResponse)
def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete document.
    """
    document = get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
        
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Delete file from disk
    from app.core.config import settings
    file_storage_path = settings.FILE_STORAGE_PATH
    file_path = os.path.join(file_storage_path, document.file_path)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete document from database
    db.delete(document)
    db.commit()
    
    return document