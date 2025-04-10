from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentCreate, DocumentUpdate


def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id).first()


def get_user_documents(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
    return db.query(Document).filter(Document.owner_id == user_id).offset(skip).limit(limit).all()


def create_document(
    db: Session, 
    document_in: DocumentCreate, 
    user_id: int,
    file_path: str,
    file_type: str,
    original_filename: str
) -> Document:
    document_data = jsonable_encoder(document_in)
    db_document = Document(
        **document_data,
        owner_id=user_id,
        file_path=file_path,
        file_type=file_type,
        original_filename=original_filename,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def update_document(db: Session, db_document: Document, document_in: DocumentUpdate) -> Document:
    document_data = jsonable_encoder(db_document)
    for field in document_data:
        if field in document_in.__fields_set__ and field != "id":
            setattr(db_document, field, getattr(document_in, field))
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def create_document_chunk(db: Session, document_id: int, content: str, chunk_index: int) -> DocumentChunk:
    db_chunk = DocumentChunk(
        document_id=document_id,
        content=content,
        chunk_index=chunk_index,
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk


def get_document_chunks(db: Session, document_id: int) -> List[DocumentChunk]:
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()