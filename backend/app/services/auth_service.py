# backend/app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import get_user_by_email

def create_access_token(
    user_id: Union[str, int], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Optional expiration time
        
    Returns:
        str: JWT token
    """
    from app.core.security import create_access_token as sec_create_access_token
    return sec_create_access_token(user_id, expires_delta)

def authenticate_user(
    db: Session, 
    email: str, 
    password: str
) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: User password
        
    Returns:
        Optional[User]: Authenticated user or None
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user_from_token(
    db: Session, 
    token: str
) -> Optional[User]:
    """
    Get current user from token.
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        Optional[User]: User or None
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        return None
    
    user = db.query(User).filter(User.id == token_data.sub).first()
    return user