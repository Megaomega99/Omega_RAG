from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# Shared properties
class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None


# Properties to receive via API on creation
class DocumentCreate(DocumentBase):
    pass


# Properties to receive via API on update
class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    is_processed: Optional[bool] = None
    is_indexed: Optional[bool] = None
    processing_status: Optional[str] = None


# Properties to return via API
class DocumentResponse(DocumentBase):
    id: int
    file_type: str
    original_filename: str
    is_processed: bool
    is_indexed: bool
    processing_status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Document chunk schema
class DocumentChunkBase(BaseModel):
    content: str
    chunk_index: int


class DocumentChunkCreate(DocumentChunkBase):
    document_id: int


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True