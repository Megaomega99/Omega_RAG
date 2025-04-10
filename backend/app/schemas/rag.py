from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class QueryInput(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    document_ids: Optional[List[int]] = None
    max_documents: Optional[int] = 5


class QueryResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int
    sources: Optional[List[Dict[str, Any]]] = None