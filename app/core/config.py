import os
from pydantic_settings import BaseSettings  # <-- Changed from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:your_new_password@localhost:5432/rag_saas"
    )
    
    # File storage
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./data")
    
    # Ollama configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama")
    
    class Config:
        case_sensitive = True

settings = Settings()