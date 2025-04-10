import os
import logging
from typing import Optional
import google.generativeai as genai
from celery.utils.log import get_task_logger
from backend.app.core.config import settings

# Configure logger
logger = get_task_logger(__name__)

# Configure Google Generative AI
GEMINI_API_KEY = settings.GEMINI_API_KEY
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Gemini functionality will not work.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure model
GEMINI_MODEL = "gemini-1.5-flash"

def get_gemini_response(prompt: str, query: str) -> Optional[str]:
    """
    Get a response from the Gemini API.
    
    Args:
        prompt (str): The context and system prompt
        query (str): The user query
        
    Returns:
        Optional[str]: The generated response or None if an error occurs
    """
    if not GEMINI_API_KEY:
        logger.error("Cannot call Gemini API: GEMINI_API_KEY is not set")
        return None
        
    try:
        # Configure the model
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract and return text
        if response and hasattr(response, 'text'):
            return response.text
        else:
            logger.error(f"Unexpected response format from Gemini: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        return None