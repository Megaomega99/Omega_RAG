import time
import os
import logging
import asyncio
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from app.db import models
from app.rag import document_processor, embeddings
from app.db import crud

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

async def process_document(document_id: int, db: Session):
    """Process a queued document."""
    try:
        # Get the document
        document = db.query(models.Document).filter(
            models.Document.id == document_id
        ).first()
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        logger.info(f"Processing document: {document.title} (ID: {document.id})")
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            logger.error(f"File not found: {document.file_path}")
            document.queued = False
            db.commit()
            return
        
        # Process the document to extract text chunks
        with open(document.file_path, "rb") as f:
            file_content = f.read()
        
        # Create a mock upload file for compatibility
        class MockUploadFile:
            def __init__(self, filename, content_type, content):
                self.filename = filename
                self.content_type = content_type
                self._content = content
            
            async def read(self):
                return self._content
        
        mock_file = MockUploadFile(
            filename=document.filename,
            content_type=document.content_type,
            content=file_content
        )
        
        # Process the document
        text_chunks = await document_processor.process_document(mock_file, document.id, db)
        
        # Generate embeddings for the chunks
        logger.info(f"Generating embeddings for {len(text_chunks)} chunks")
        for chunk in text_chunks:
            chunk_embedding = embeddings.generate_embeddings([chunk])[0]
            crud.create_document_chunk(db, chunk, chunk_embedding, document.id)
        
        # Mark document as processed
        document.processed = True
        document.queued = False
        db.commit()
        
        logger.info(f"Document processed: {document.title} (ID: {document.id})")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        try:
            # Mark as not queued in case of error
            document = db.query(models.Document).filter(
                models.Document.id == document_id
            ).first()
            if document:
                document.queued = False
                db.commit()
        except:
            pass

async def worker_loop():
    """Main worker loop that processes queued documents."""
    logger.info("Starting worker loop")
    
    while True:
        try:
            db = get_db()
            
            # Get queued documents that are not processed
            queued_documents = db.query(models.Document).filter(
                models.Document.queued == True,
                models.Document.processed == False
            ).all()
            
            for document in queued_documents:
                await process_document(document.id, db)
            
            db.close()
            
            # Sleep before checking again
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}")
            await asyncio.sleep(30)  # Sleep longer on error

if __name__ == "__main__":
    # Start the worker loop
    asyncio.run(worker_loop())