from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext
from fastapi import HTTPException
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    db_user = models.User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Document operations
def create_document(db: Session, title: str, filename: str, file_path: str, content_type: str, owner_id: int):
    db_document = models.Document(
        title=title,
        filename=filename,
        file_path=file_path,
        content_type=content_type,
        owner_id=owner_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_documents(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Document).filter(models.Document.owner_id == owner_id).offset(skip).limit(limit).all()

def get_document(db: Session, document_id: int, owner_id: int):
    return db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.owner_id == owner_id
    ).first()

def delete_document(db: Session, document_id: int, owner_id: int):
    db_document = get_document(db, document_id, owner_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete associated chunks
    db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == document_id
    ).delete()
    
    # Delete document from database
    db.delete(db_document)
    
    # Delete file from disk
    if os.path.exists(db_document.file_path):
        os.remove(db_document.file_path)
    
    db.commit()
    return {"success": True}

# Document chunks operations
def create_document_chunk(db: Session, content: str, embedding, document_id: int):
    db_chunk = models.DocumentChunk(
        content=content,
        embedding=embedding,
        document_id=document_id
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

def get_all_chunks(db: Session):
    return db.query(models.DocumentChunk).all()

# Query operations
def save_query(db: Session, question: str, answer: str, user_id: int):
    db_query = models.Query(
        question=question,
        answer=answer,
        user_id=user_id
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

def get_user_queries(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Query).filter(
        models.Query.user_id == user_id
    ).order_by(models.Query.created_at.desc()).offset(skip).limit(limit).all()