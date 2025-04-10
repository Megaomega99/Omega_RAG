import os
import re
import logging
from typing import List, Optional
from celery.utils.log import get_task_logger

# Configure logger
logger = get_task_logger(__name__)

def extract_text_from_document(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract text from various document formats.
    
    Args:
        file_path (str): Path to the document file
        file_type (str): Type of the file (pdf, txt, docx, md)
        
    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    try:
        if file_type == "pdf":
            return extract_text_from_pdf(file_path)
        elif file_type == "txt":
            return extract_text_from_txt(file_path)
        elif file_type == "docx":
            return extract_text_from_docx(file_path)
        elif file_type == "md":
            return extract_text_from_markdown(file_path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import pdfplumber
        text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
                
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        # Fallback to unstructured
        try:
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(file_path)
            return "\n\n".join([str(element) for element in elements])
        except Exception as fallback_e:
            logger.error(f"Fallback extraction failed for PDF {file_path}: {str(fallback_e)}")
            raise

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a TXT file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    import docx
    doc = docx.Document(file_path)
    return "\n\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_markdown(file_path: str) -> str:
    """Extract text from a Markdown file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        md_text = f.read()
    
    # Remove Markdown formatting (basic)
    md_text = re.sub(r'##+\s', '', md_text)  # Remove headings
    md_text = re.sub(r'\*\*(.*?)\*\*', r'\1', md_text)  # Remove bold
    md_text = re.sub(r'\*(.*?)\*', r'\1', md_text)  # Remove italic
    md_text = re.sub(r'```.*?```', '', md_text, flags=re.DOTALL)  # Remove code blocks
    
    return md_text

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text (str): The text to chunk
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Split text into paragraphs
    paragraphs = text.split("\n\n")
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, add current chunk to chunks
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep some overlap for context
            current_chunk = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
        
        # Add paragraph to current chunk
        if current_chunk:
            current_chunk += "\n\n" + paragraph
        else:
            current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Handle case where a single paragraph exceeds chunk size
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            # Split by sentences for large paragraphs
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
        else:
            final_chunks.append(chunk)
    
    return final_chunks