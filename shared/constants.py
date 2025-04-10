# shared/constants.py
"""
Shared constants for the Omega RAG application.
"""

# Application constants
APP_NAME = "Omega RAG"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Retrieval Augmented Generation SaaS Application"

# Document processing constants
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".txt", ".docx", ".md"]
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
MAX_DOCUMENT_SIZE_MB = 50

# RAG constants
DEFAULT_MAX_DOCUMENTS = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.7
EMBEDDING_DIMENSION = 768  # For Gemini embeddings

# User roles
ROLE_USER = "user"
ROLE_ADMIN = "admin"

# Document processing status
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Message roles
ROLE_USER_MESSAGE = "user"
ROLE_ASSISTANT_MESSAGE = "assistant"

# System prompts
RAG_SYSTEM_PROMPT = """You are an AI assistant that helps users with their documents. 
Answer the following question based on the provided context information and previous conversation. 
If the context doesn't contain relevant information, just say that you don't have enough information to answer accurately."""

# Frontend constants
DEFAULT_THEME_COLOR = "#1565C0"  # Blue 800