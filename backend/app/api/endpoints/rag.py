from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.schemas.rag import QueryInput, QueryResponse
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageResponse

from worker.tasks.rag_tasks import generate_rag_response

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(
    *,
    db: Session = Depends(get_db),
    query_input: QueryInput,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Query the RAG system with a question.
    """
    # Validate conversation if provided
    conversation = None
    if query_input.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == query_input.conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
            
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    else:
        # Create a new conversation
        conversation = Conversation(
            title=query_input.query[:50] + "..." if len(query_input.query) > 50 else query_input.query,
            user_id=current_user.id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Validate documents if provided
    if query_input.document_ids:
        documents = db.query(Document).filter(
            Document.id.in_(query_input.document_ids),
            Document.is_processed == True,
            Document.is_indexed == True
        ).all()
        
        if len(documents) != len(query_input.document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more documents are not found or not processed",
            )
            
        for doc in documents:
            if doc.owner_id != current_user.id and not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions for document {doc.id}",
                )
    
    # Create message
    user_message = Message(
        conversation_id=conversation.id,
        content=query_input.query,
        role="user"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Create placeholder for assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        content="Processing your query...",
        role="assistant"
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    # Call RAG task
    task = generate_rag_response.delay(
        query=query_input.query,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        document_ids=query_input.document_ids,
        max_documents=query_input.max_documents
    )
    
    # For now, return a simple response (the actual response will be updated by the task)
    return QueryResponse(
        response="Your query is being processed. Please check the conversation for the response.",
        conversation_id=conversation.id,
        message_id=assistant_message.id
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get user's conversations.
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific conversation.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
        
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    # Load messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()
    
    conversation.messages = messages
    
    return conversation