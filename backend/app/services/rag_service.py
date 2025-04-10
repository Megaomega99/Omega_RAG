# backend/app/services/rag_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.schemas.rag import QueryInput
from app.core.exceptions import RAGQueryError

def create_conversation(
    db: Session, 
    title: str, 
    user_id: int
) -> Conversation:
    """
    Create a new conversation.
    
    Args:
        db: Database session
        title: Conversation title
        user_id: User ID
        
    Returns:
        Conversation: Created conversation
    """
    conversation = Conversation(
        title=title,
        user_id=user_id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_conversation_by_id(
    db: Session, 
    conversation_id: int
) -> Optional[Conversation]:
    """
    Get conversation by ID.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        
    Returns:
        Optional[Conversation]: Conversation or None
    """
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def get_user_conversations(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Conversation]:
    """
    Get user's conversations.
    
    Args:
        db: Database session
        user_id: User ID
        skip: Pagination offset
        limit: Pagination limit
        
    Returns:
        List[Conversation]: List of conversations
    """
    return db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

def create_message(
    db: Session, 
    conversation_id: int, 
    content: str, 
    role: str, 
    context_documents: Optional[Dict[str, Any]] = None
) -> Message:
    """
    Create a new message.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        content: Message content
        role: Message role (user/assistant)
        context_documents: Optional context documents
        
    Returns:
        Message: Created message
    """
    message = Message(
        conversation_id=conversation_id,
        content=content,
        role=role,
        context_documents=context_documents
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_conversation_messages(
    db: Session, 
    conversation_id: int
) -> List[Message]:
    """
    Get messages for a conversation.
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        
    Returns:
        List[Message]: List of messages
    """
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

def update_message(
    db: Session, 
    message_id: int, 
    content: str, 
    context_documents: Optional[Dict[str, Any]] = None
) -> Optional[Message]:
    """
    Update a message.
    
    Args:
        db: Database session
        message_id: Message ID
        content: New content
        context_documents: New context documents
        
    Returns:
        Optional[Message]: Updated message or None
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return None
        
    message.content = content
    if context_documents is not None:
        message.context_documents = context_documents
        
    db.commit()
    db.refresh(message)
    return message

def validate_rag_query(
    db: Session, 
    query_input: QueryInput, 
    user_id: int
) -> Dict[str, Any]:
    """
    Validate a RAG query input.
    
    Args:
        db: Database session
        query_input: Query input
        user_id: User ID
        
    Returns:
        Dict[str, Any]: Validation result
    """
    result = {
        "is_valid": True,
        "conversation": None,
        "documents": [],
        "errors": []
    }
    
    # Validate conversation if provided
    if query_input.conversation_id:
        conversation = get_conversation_by_id(db, query_input.conversation_id)
        
        if not conversation:
            result["is_valid"] = False
            result["errors"].append("Conversation not found")
            return result
            
        if conversation.user_id != user_id:
            result["is_valid"] = False
            result["errors"].append("Not enough permissions for this conversation")
            return result
            
        result["conversation"] = conversation
    
    # Validate documents if provided
    if query_input.document_ids:
        documents = db.query(Document).filter(
            Document.id.in_(query_input.document_ids),
            Document.is_processed == True,
            Document.is_indexed == True
        ).all()
        
        if len(documents) != len(query_input.document_ids):
            result["is_valid"] = False
            result["errors"].append("One or more documents are not found or not processed")
            return result
            
        for doc in documents:
            if doc.owner_id != user_id:
                result["is_valid"] = False
                result["errors"].append(f"Not enough permissions for document {doc.id}")
                return result
                
        result["documents"] = documents
    
    return result