import os
import re
from typing import List, Optional
from fastapi import UploadFile, HTTPException
import PyPDF2
from docx import Document as DocxDocument
import markdown
from pathlib import Path
from app.core.config import settings

# Function to create chunks of text
def create_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    # Clean text - remove extra spaces and line breaks
    text = re.sub(r'\s+', ' ', text).strip()
    
    # If text is smaller than chunk size, return as is
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Get the end position for the current chunk
        end = start + chunk_size
        
        # If we're not at the end of the text, try to break at a period or space
        if end < len(text):
            # Try to find a period followed by a space near the end of the chunk
            period_pos = text.rfind('. ', start, end)
            if period_pos != -1 and period_pos > start + chunk_size // 2:
                end = period_pos + 1  # Include the period
            else:
                # If no suitable period found, try to break at a space
                space_pos = text.rfind(' ', start, end)
                if space_pos != -1:
                    end = space_pos
        
        # Add the chunk to our list
        chunks.append(text[start:end].strip())
        
        # Move the start position, considering overlap
        start = end - overlap if end - overlap > start else end
    
    return chunks

# Function to extract text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to extract text from markdown
def extract_text_from_markdown(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()
    
    # Convert markdown to HTML and then extract text
    html_content = markdown.markdown(md_content)
    
    # Basic HTML tag removal (this is a simple approach, consider using a proper HTML parser for more complex documents)
    text = re.sub(r'<[^>]+>', ' ', html_content)
    return text

# Function to extract text from TXT
def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Main function to process uploaded document
async def process_document(file: UploadFile, document_id: int, db_session) -> List[str]:
    """Process the uploaded document and return chunks of text."""
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    
    # Define file path
    file_path = os.path.join(settings.UPLOAD_FOLDER, f"{document_id}_{file.filename}")
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Update document with file path
    from app.db import crud, models
    document = db_session.query(models.Document).filter(models.Document.id == document_id).first()
    document.file_path = file_path
    db_session.commit()
    
    # Process document based on content type
    try:
        content_type = file.content_type
        
        if "pdf" in content_type or file_path.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif "word" in content_type or file_path.endswith(".docx"):
            text = extract_text_from_docx(file_path)
        elif "markdown" in content_type or file_path.endswith(".md"):
            text = extract_text_from_markdown(file_path)
        elif "text/plain" in content_type or file_path.endswith(".txt"):
            text = extract_text_from_txt(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
        
        # Create text chunks
        chunks = create_chunks(text)
        
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")