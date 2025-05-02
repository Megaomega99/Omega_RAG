from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings

# Ensure data directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# Install pg8000 for Cloud SQL connectivity
# If using Cloud SQL Auth Proxy, use psycopg2
# pip install pg8000==1.29.0

# Create database engine with appropriate connection string
if settings.USE_CLOUD_SQL_AUTH_PROXY:
    # For connecting through Cloud SQL Auth Proxy
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800
    )
else:
    # For connecting directly to Cloud SQL
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()