import os
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np

from celery import shared_task
from celery.utils.log import get_task_logger

from worker.main import celery
from worker.llm.gemini_client import get_gemini_response
from worker.llm.embedding import generate_embeddings, cosine_similarity
from backend.app.db.session import SessionLocal
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.conversation import Conversation, Message
from backend.app.core.config import settings

logger = get_task_logger(__name__)


def retrieve_relevant_chunks(
    db: Session, 
    query: str, 
    document_ids: Optional[List[int]] = None,
    max_chunks: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks for a given query.
    """
    # Generate query embedding
    query_embedding = generate_embeddings(query)
    
    # Get document chunks based on document_ids or all indexed documents
    chunk_query = db.query(DocumentChunk)
    
    if document_ids:
        chunk_query = chunk_query.join(Document).filter(
            Document.id.in_(document_ids),
            Document.is_indexed == True
        )
    else:
        chunk_query = chunk_query.join(Document).filter(
            Document.is_indexed == True
        )
    
    chunks = chunk_query.all()
    
    # Calculate similarity scores
    chunks_with_scores = []
    
    for chunk in chunks:
        # Skip chunks without embeddings
        if not chunk.embedding_path:
            continue
            
        # Load embedding from disk
        embedding_path = os.path.join(settings.FILE_STORAGE_PATH, chunk.embedding_path)
        
        if not os.path.exists(embedding_path):
            logger.warning(f"Embedding file not found: {embedding_path}")
            continue
            
        try:
            chunk_embedding = np.load(embedding_path)
            
            # Calculate similarity
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            
            chunks_with_scores.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "similarity": similarity
            })
        except Exception as e:
            logger.error(f"Error loading embedding {embedding_path}: {str(e)}")
    
    # Sort by similarity score
    sorted_chunks = sorted(chunks_with_scores, key=lambda x: x["similarity"], reverse=True)
    
    # Return top chunks
    return sorted_chunks[:max_chunks]


@shared_task(name="generate_rag_response")
def generate_rag_response(
    query: str,
    conversation_id: int,
    message_id: int,
    document_ids: Optional[List[int]] = None,
    max_documents: int = 5
) -> Dict[str, Any]:
    """
    Generate a RAG response for a given query.
    """
    db = SessionLocal()
    try:
        # Get conversation and message
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        message = db.query(Message).filter(Message.id == message_id).first()
        
        if not conversation or not message:
            logger.error(f"Conversation {conversation_id} or message {message_id} not found")
            return {"success": False, "error": "Conversation or message not found"}
        
        # Get conversation history
        history = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.id != message_id
        ).order_by(Message.created_at.asc()).all()
        
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(
            db=db,
            query=query,
            document_ids=document_ids,
            max_chunks=max_documents
        )
        
        # Build context string
        context = "Context information:\n\n"
        sources = []
        
        for i, chunk in enumerate(relevant_chunks):
            # Get document info
            document = db.query(Document).filter(Document.id == chunk["document_id"]).first()
            if document:
                context += f"[Document {i+1}: {document.title}]\n{chunk['content']}\n\n"
                sources.append({
                    "document_id": document.id,
                    "document_title": document.title,
                    "chunk_id": chunk["chunk_id"],
                    "similarity": float(chunk["similarity"])
                })
        
        # Build conversation history
        conversation_context = ""
        if history:
            conversation_context = "Previous conversation:\n\n"
            for msg in history:
                role = "Human" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n\n"
        
        # Build prompt for Gemini
        prompt = f"""You are an AI assistant that helps users with their documents. Answer the following question based on the provided context information and previous conversation. If the context doesn't contain relevant information, just say that you don't have enough information to answer accurately.

{context}

{conversation_context}

Human question: {query}

Answer the question precisely based on the context. If the context doesn't have relevant information, acknowledge this and suggest what additional information might be helpful."""

        # Get response from Gemini
        response = get_gemini_response(prompt, query)
        
        if not response:
            logger.error(f"Failed to get response from Gemini for query: {query}")
            response = "I'm sorry, but I encountered an issue while processing your query. Please try again later."
        
        # Update assistant message
        message.content = response
        message.context_documents = sources
        db.commit()
        
        return {
            "success": True,
            "response": response,
            "conversation_id": conversation.id,
            "message_id": message.id,
            "sources": sources
        }
    
    except Exception as e:
        logger.error(f"Error generating RAG response: {str(e)}")
        
        # Update message with error
        if message:
            message.content = "I'm sorry, but an error occurred while processing your query. Please try again later."
            db.commit()
        
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()