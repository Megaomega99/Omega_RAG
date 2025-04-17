from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db import crud, models
from app.rag import document_processor, embeddings

router = APIRouter()

async def process_document_task(document_id: int, file: UploadFile, db: Session):
    """Background task to process a document after upload."""
    # Process the document to extract text chunks
    text_chunks = await document_processor.process_document(file, document_id, db)
    
    # Generate embeddings for the chunks
    for chunk in text_chunks:
        chunk_embedding = embeddings.generate_embeddings([chunk])[0]
        crud.create_document_chunk(db, chunk, chunk_embedding, document_id)
    
    # Mark document as processed
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    document.processed = True
    db.commit()

@router.post("/")
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Upload a new document for processing."""
    # Create document record
    document = crud.create_document(
        db, 
        title=title, 
        filename=file.filename, 
        file_path="", 
        content_type=file.content_type, 
        owner_id=current_user.id
    )
    
    # Process document in background
    background_tasks.add_task(process_document_task, document.id, file, db)
    
    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "status": "processing"
    }

@router.get("/")
def get_user_documents(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> List[Any]:
    """Get all documents for the current user."""
    documents = crud.get_documents(db, current_user.id, skip, limit)
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "processed": doc.processed,
            "created_at": doc.created_at
        }
        for doc in documents
    ]

@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Get a specific document by ID."""
    document = crud.get_document(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "processed": document.processed,
        "created_at": document.created_at,
        "chunk_count": len(document.chunks)
    }

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Delete a document by ID."""
    return crud.delete_document(db, document_id, current_user.id)