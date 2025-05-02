import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # GCP Instance IPs
    FILE_SERVER_INTERNAL_IP: str = os.getenv("FILE_SERVER_INTERNAL_IP", "10.128.0.8")
    FILE_SERVER_EXTERNAL_IP: str = os.getenv("FILE_SERVER_EXTERNAL_IP", "35.232.252.195")
    WEB_SERVER_INTERNAL_IP: str = os.getenv("WEB_SERVER_INTERNAL_IP", "10.128.0.9")
    WORKER_INTERNAL_IP: str = os.getenv("WORKER_INTERNAL_IP", "10.128.0.10")
    
    # Cloud SQL PostgreSQL configuration
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "your_new_password")
    DB_NAME: str = os.getenv("DB_NAME", "rag_saas")
    DB_INSTANCE_CONNECTION_NAME: str = os.getenv("DB_INSTANCE_CONNECTION_NAME", "")
    USE_CLOUD_SQL_AUTH_PROXY: bool = os.getenv("USE_CLOUD_SQL_AUTH_PROXY", "False").lower() == "true"
    
    # Construct DATABASE_URL
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_CLOUD_SQL_AUTH_PROXY:
            # For connecting through Cloud SQL Auth Proxy
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            # Direct connection to Cloud SQL (using socket)
            return f"postgresql+pg8000://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}?unix_sock=/cloudsql/{self.DB_INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
    
    # File storage
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "/mnt/filestore")
    FILE_SERVER_URL: str = os.getenv("FILE_SERVER_URL", f"http://{FILE_SERVER_INTERNAL_IP}:8080")
    
    # Ollama configuration (running on worker instance)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", f"http://{WORKER_INTERNAL_IP}:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama")
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", f"http://{FILE_SERVER_EXTERNAL_IP}:7000")
    
    class Config:
        case_sensitive = True

settings = Settings()