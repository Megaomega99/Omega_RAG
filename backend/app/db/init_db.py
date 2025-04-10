import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate

# Import all models to ensure they are registered with SQLAlchemy
from app.models import user, document, conversation

logger = logging.getLogger(__name__)

def init_db() -> None:
    db = SessionLocal()
    try:
        # Create a default admin user if no users exist
        user_count = db.query(User).count()
        if user_count == 0:
            user_in = UserCreate(
                email="admin@omega-rag.com",
                password="admin123",  # In production, use a strong password
                full_name="Admin User",
                is_admin=True,
            )
            db_user = User(
                email=user_in.email,
                hashed_password=get_password_hash(user_in.password),
                full_name=user_in.full_name,
                is_admin=user_in.is_admin,
            )
            db.add(db_user)
            db.commit()
            logger.info("Created initial admin user")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()