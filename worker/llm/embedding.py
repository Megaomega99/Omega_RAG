import os
import numpy as np
from typing import List, Optional
import google.generativeai as genai
from celery.utils.log import get_task_logger

from backend.app.core.config import settings

# Configure logger
logger = get_task_logger(__name__)

# Configure Google Generative AI
# Prioritize environment variable over settings from backend
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Embedding functionality will not work.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for text using Google Generative AI.
    
    Args:
        text (str): The text to generate embeddings for
        
    Returns:
        List[float]: The embedding vector
    """
    if not GEMINI_API_KEY:
        # Generate random embeddings as fallback for testing
        logger.warning("Using random embeddings as fallback (GEMINI_API_KEY not set)")
        return list(np.random.random(768))  # Standard dimension
    
    try:
        # Generate embeddings using Google's embedding model
        embedding_model = "models/embedding-001"
        embedding = genai.embed_content(
            model=embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        
        if hasattr(embedding, 'embedding'):
            return embedding.embedding
        else:
            logger.error(f"Unexpected embedding format: {embedding}")
            return list(np.random.random(768))  # Fallback
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        # Fallback to random embeddings for testing
        return list(np.random.random(768))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a (List[float]): First vector
        b (List[float]): Second vector
        
    Returns:
        float: Cosine similarity score
    """
    a = np.array(a)
    b = np.array(b)
    
    # Avoid division by zero
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0
        
    return np.dot(a, b) / (norm_a * norm_b)