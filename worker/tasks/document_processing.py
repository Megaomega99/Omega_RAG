import os
import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from celery import shared_task
from celery.utils.log import get_task_logger

from worker.main import celery
from worker.llm.text_processing import extract_text_from_document, chunk_text
from worker.llm.embedding import generate_embeddings
from backend.app.db.session import SessionLocal
from backend.app.models.document import Document, DocumentChunk
from backend.app.core.config import settings

logger = get_task_logger(__name__)


@shared_task(name="process_document")
def process_document(document_id: int) -> Dict[str, Any]:
    """
    Process a document by extracting text, chunking, and generating embeddings.
    """
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"success": False, "error": "Document not found"}
        
        # Update document status
        document.processing_status = "processing"
        db.commit()
        
        # Get document path
        file_path = os.path.join(settings.FILE_STORAGE_PATH, document.file_path)
        if not os.path.exists(file_path):
            logger.error(f"File not found at {file_path}")
            document.processing_status = "failed"
            db.commit()
            return {"success": False, "error": "File not found"}
        
        # Extract text based on file type
        try:
            text = extract_text_from_document(file_path, document.file_type)
            
            if not text:
                logger.error(f"Failed to extract text from document {document_id}")
                document.processing_status = "failed"
                db.commit()
                return {"success": False, "error": "Failed to extract text"}
            
            # Chunk text
            chunks = chunk_text(text)
            
            # Create embeddings directory if it doesn't exist
            embeddings_dir = os.path.join(settings.FILE_STORAGE_PATH, "embeddings")
            os.makedirs(embeddings_dir, exist_ok=True)
            
            # Store chunks and generate embeddings
            for i, chunk in enumerate(chunks):
                # Create chunk in database
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk,
                    chunk_index=i
                )
                db.add(db_chunk)
                db.commit()
                db.refresh(db_chunk)
                
                # Generate embedding
                try:
                    embeddings = generate_embeddings(chunk)
                    
                    # Save embedding to disk
                    embedding_filename = f"doc_{document.id}_chunk_{db_chunk.id}.npy"
                    embedding_path = os.path.join(embeddings_dir, embedding_filename)
                    
                    import numpy as np
                    np.save(embedding_path, np.array(embeddings))
                    
                    # Update chunk with embedding path
                    db_chunk.embedding_path = f"embeddings/{embedding_filename}"
                    db.commit()
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {db_chunk.id}: {str(e)}")
            
            # Update document status
            document.is_processed = True
            document.is_indexed = True
            document.processing_status = "completed"
            db.commit()
            
            return {
                "success": True,
                "document_id": document.id,
                "chunks_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            document.processing_status = "failed"
            db.commit()
            return {"success": False, "error": str(e)}
    
    finally:
        db.close()