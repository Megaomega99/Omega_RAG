import re
import tiktoken
from typing import List, Dict, Any, Optional, Callable
from celery.utils.log import get_task_logger

# Configure logger
logger = get_task_logger(__name__)

def chunk_text_by_tokens(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    model_name: str = "gpt-3.5-turbo"
) -> List[str]:
    """
    Split text into chunks based on token count rather than character count.
    This is more accurate for LLM context windows.
    
    Args:
        text (str): The text to chunk
        chunk_size (int): Maximum number of tokens per chunk
        chunk_overlap (int): Number of overlapping tokens between chunks
        model_name (str): Model name for tokenizer selection
        
    Returns:
        List[str]: List of text chunks with token counts respecting chunk_size
    """
    try:
        # Get the appropriate tokenizer
        tokenizer = tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base tokenizer (used by GPT-4 and ChatGPT)
        logger.warning(f"Tokenizer for {model_name} not found, using cl100k_base")
        tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # Tokenize the text
    tokens = tokenizer.encode(text)
    
    # Split into chunks
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        # Calculate end index for this chunk
        end_idx = min(start_idx + chunk_size, len(tokens))
        
        # Get the token IDs for this chunk
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode the tokens back to text
        chunk_text = tokenizer.decode(chunk_tokens)
        
        # Add the chunk to the list
        chunks.append(chunk_text)
        
        # Move the start index for the next chunk, considering overlap
        if end_idx == len(tokens):
            # We've reached the end of the text
            break
            
        start_idx = end_idx - chunk_overlap
    
    return chunks

def chunk_by_markdown_headers(
    text: str,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100
) -> List[str]:
    """
    Split markdown text by headers and further chunk if sections are too long.
    
    Args:
        text (str): Markdown text to chunk
        max_chunk_size (int): Maximum characters per chunk
        min_chunk_size (int): Minimum characters per chunk (to avoid tiny chunks)
        
    Returns:
        List[str]: List of markdown chunks
    """
    # Pattern to match headers (ATX style)
    header_pattern = r'(^|\n)(#{1,6}\s+[^\n]+)'
    
    # Find all headers
    header_matches = list(re.finditer(header_pattern, text))
    
    # If no headers found, use character chunking
    if not header_matches:
        return chunk_text(text, max_chunk_size, max_chunk_size // 5)
    
    chunks = []
    last_end = 0
    
    # Process each header section
    for i, match in enumerate(header_matches):
        # Get the start of this header
        section_start = match.start()
        
        # If this is not the first header and there's content before it
        if section_start > last_end:
            # Add the content before this header as a chunk
            content_before = text[last_end:section_start]
            if len(content_before) > min_chunk_size:
                chunks.append(content_before)
        
        # Determine the end of this section (start of next header or end of text)
        section_end = header_matches[i+1].start() if i < len(header_matches)-1 else len(text)
        
        # Get the section text (including the header)
        section_text = text[section_start:section_end]
        
        # If the section is too large, sub-chunk it
        if len(section_text) > max_chunk_size:
            # Get the header text
            header_text = match.group(2)
            
            # Split the section content (excluding the header)
            section_content = text[match.end():section_end]
            
            # Chunk the section content
            content_chunks = chunk_text(section_content, max_chunk_size - len(header_text) - 2, 
                                     (max_chunk_size - len(header_text) - 2) // 5)
            
            # Add the header to each chunk
            for content_chunk in content_chunks:
                chunks.append(f"{header_text}\n\n{content_chunk}")
        else:
            # Add the section as a single chunk
            chunks.append(section_text)
        
        last_end = section_end
    
    # If there's content after the last header
    if last_end < len(text):
        remaining = text[last_end:]
        if len(remaining) > min_chunk_size:
            chunks.append(remaining)
    
    return chunks

def chunk_text(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200,
    separator: str = "\n\n"
) -> List[str]:
    """
    Split text into overlapping chunks, preserving semantic boundaries when possible.
    
    Args:
        text (str): The text to chunk
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Overlap between chunks
        separator (str): Preferred separator for chunk boundaries
        
    Returns:
        List[str]: List of text chunks
    """
    # Split text by separator
    segments = text.split(separator)
    
    chunks = []
    current_chunk = ""
    
    for segment in segments:
        # If adding this segment would exceed chunk size
        if len(current_chunk) + len(segment) + len(separator) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep some overlap for context
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                # Try to find a clean separator within the overlap region
                overlap_text = current_chunk[-chunk_overlap:]
                sep_index = overlap_text.find(separator)
                
                if sep_index != -1:
                    # Found a separator in the overlap region
                    current_chunk = current_chunk[-(chunk_overlap - sep_index):]
                else:
                    # No separator found, use the last N characters
                    current_chunk = current_chunk[-chunk_overlap:]
            else:
                current_chunk = ""
        
        # Add segment to current chunk
        if current_chunk:
            current_chunk += separator + segment
        else:
            current_chunk = segment
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Handle case where individual segments exceed chunk size
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            # For large chunks, split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            sub_chunk = ""
            
            for sentence in sentences:
                if len(sub_chunk) + len(sentence) > chunk_size and sub_chunk:
                    final_chunks.append(sub_chunk.strip())
                    sub_chunk = sentence
                else:
                    if sub_chunk:
                        sub_chunk += " " + sentence
                    else:
                        sub_chunk = sentence
            
            if sub_chunk:
                final_chunks.append(sub_chunk.strip())
                
            # Last resort: if sentences are still too long, split by character
            for i, fc in enumerate(final_chunks):
                if len(fc) > chunk_size:
                    # Replace with character-level chunks
                    char_chunks = [fc[j:j+chunk_size] for j in range(0, len(fc), chunk_size - chunk_overlap)]
                    final_chunks[i:i+1] = char_chunks
        else:
            final_chunks.append(chunk)
    
    return final_chunks