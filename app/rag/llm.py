import requests
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings

def query_ollama(
    prompt: str,
    model: str = settings.OLLAMA_MODEL,
    context: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """Query the Ollama API with a prompt and optional context."""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    # Prepare the request data
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }
    
    # Add context if provided
    if context:
        data["context"] = context
    
    try:
        # Make the request to Ollama
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        print(f"Error querying Ollama: {str(e)}")
        return f"Error: Could not get a response from the language model. {str(e)}"

def generate_rag_response(query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
    """Generate a response using RAG (Retrieval Augmented Generation)."""
    # Extract and format the context from relevant chunks
    context_text = "\n\n".join([chunk.get("content", "") for chunk in relevant_chunks])
    
    # Create the prompt with context
    prompt = f"""Given the following context, please answer the question. 
    If the context doesn't contain enough information to answer the question completely, 
    just say what you know based on the context and don't make up information.

    Context:
    {context_text}

    Question: {query}

    Answer:"""
    
    # Query the LLM
    response = query_ollama(prompt=prompt)
    
    return response