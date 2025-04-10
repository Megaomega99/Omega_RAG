# backend/app/core/exceptions.py
from fastapi import HTTPException, status

class DocumentProcessingError(Exception):
    """Exception raised when document processing fails."""
    pass

class RAGQueryError(Exception):
    """Exception raised when RAG query processing fails."""
    pass

class FileStorageError(Exception):
    """Exception raised for file storage related errors."""
    pass

# HTTP Exceptions for API responses
DocumentNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Document not found"
)

NotEnoughPermissions = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions"
)

UserNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found"
)

InvalidCredentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password"
)

InactiveUser = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Inactive user"
)

EmailAlreadyExists = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="The user with this email already exists in the system"
)