from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model for embeddings

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of text chunks."""
    try:
        embeddings = model.encode(texts)
        return embeddings.tolist()
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return [[] for _ in texts]  # Return empty embeddings on error

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2:  # Handle empty vectors
        return 0.0
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

def find_relevant_chunks(
    query_embedding: List[float],
    all_chunks: List[Dict[str, Any]],
    top_k: int = 5,
    threshold: float = 0.25
) -> List[Dict[str, Any]]:
    """Find chunks most relevant to the query."""
    if not query_embedding or not all_chunks:
        return []
    
    # Calculate similarity scores
    similarities = []
    for chunk in all_chunks:
        embedding = chunk.get("embedding", [])
        if embedding:
            similarity = cosine_similarity(query_embedding, embedding)
            similarities.append((chunk, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top K chunks above threshold
    return [chunk for chunk, score in similarities[:top_k] if score >= threshold]