from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# Message schemas
class MessageBase(BaseModel):
    content: str
    role: str


class MessageCreate(MessageBase):
    conversation_id: int
    context_documents: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    context_documents: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Conversation schemas
class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(ConversationBase):
    title: Optional[str] = None


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True