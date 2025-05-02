import requests
import json
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def query_ollama(
    prompt: str,
    model: str = settings.OLLAMA_MODEL,
    context: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    retry_count: int = 3
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
    
    # Implement retry logic for GCP environment
    attempts = 0
    while attempts < retry_count:
        try:
            # Make the request to Ollama
            logger.info(f"Sending request to Ollama at {url}")
            response = requests.post(url, json=data, timeout=60)  # Added timeout
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError as ce:
            attempts += 1
            logger.error(f"Connection error to Ollama (attempt {attempts}/{retry_count}): {str(ce)}")
            if attempts >= retry_count:
                return f"Error: Could not connect to the language model. Please try again later."
        except requests.exceptions.Timeout as te:
            attempts += 1
            logger.error(f"Timeout error to Ollama (attempt {attempts}/{retry_count}): {str(te)}")
            if attempts >= retry_count:
                return f"Error: The language model took too long to respond. Please try again later."
        except Exception as e:
            attempts += 1
            logger.error(f"Error querying Ollama (attempt {attempts}/{retry_count}): {str(e)}")
            if attempts >= retry_count:
                return f"Error: Could not get a response from the language model. Please try again later."

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