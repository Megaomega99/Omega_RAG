import os
import uuid
import shutil
from typing import Dict, List, Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

from app.core.config import settings


def validate_file_extension(filename: str, allowed_extensions: List[str] = None) -> Tuple[bool, str]:
    """
    Validate file extension against a list of allowed extensions.
    
    Args:
        filename (str): Original filename
        allowed_extensions (List[str], optional): List of allowed extensions with dot, e.g. ['.pdf', '.txt']
            Defaults to ['.pdf', '.txt', '.docx', '.md']
    
    Returns:
        Tuple[bool, str]: (is_valid, extension)
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.txt', '.docx', '.md']
    
    # Get file extension
    ext = os.path.splitext(filename.lower())[1]
    
    # Check if extension is allowed
    if ext not in allowed_extensions:
        return False, ext
        
    return True, ext


def save_uploaded_file(file: UploadFile, subdir: str = "") -> Tuple[str, str]:
    """
    Save an uploaded file to disk and return the saved path and file type.
    
    Args:
        file (UploadFile): FastAPI UploadFile object
        subdir (str, optional): Subdirectory within storage path. Defaults to "".
    
    Returns:
        Tuple[str, str]: (unique_filename, file_type)
    """
    # Validate file extension
    is_valid, ext = validate_file_extension(file.filename)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not supported. Allowed types: .pdf, .txt, .docx, .md"
        )
    
    # Create directory if it doesn't exist
    storage_path = settings.FILE_STORAGE_PATH
    if subdir:
        storage_path = os.path.join(storage_path, subdir)
        
    os.makedirs(storage_path, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(storage_path, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    # Return unique filename (without path) and file type
    file_type = ext.replace(".", "")
    return unique_filename, file_type


def get_file_path(filename: str, subdir: str = "") -> str:
    """
    Get the full path to a file in the storage directory.
    
    Args:
        filename (str): Filename (without path)
        subdir (str, optional): Subdirectory within storage path. Defaults to "".
    
    Returns:
        str: Full file path
    """
    storage_path = settings.FILE_STORAGE_PATH
    if subdir:
        storage_path = os.path.join(storage_path, subdir)
        
    return os.path.join(storage_path, filename)


def delete_file(filename: str, subdir: str = "") -> bool:
    """
    Delete a file from the storage directory.
    
    Args:
        filename (str): Filename (without path)
        subdir (str, optional): Subdirectory within storage path. Defaults to "".
    
    Returns:
        bool: True if file was deleted, False otherwise
    """
    file_path = get_file_path(filename, subdir)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def scan_directory(directory: str, recursive: bool = False) -> List[Dict[str, str]]:
    """
    Scan a directory and return a list of files with metadata.
    
    Args:
        directory (str): Directory to scan
        recursive (bool, optional): Whether to scan subdirectories. Defaults to False.
    
    Returns:
        List[Dict[str, str]]: List of file information dictionaries
    """
    result = []
    
    try:
        # Get the full path
        full_path = os.path.join(settings.FILE_STORAGE_PATH, directory)
        
        # Check if directory exists
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return result
            
        # Walk through the directory
        if recursive:
            for root, _, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, full_path)
                    
                    result.append({
                        "filename": file,
                        "path": rel_path,
                        "size": os.path.getsize(file_path),
                        "extension": os.path.splitext(file)[1].lower(),
                    })
        else:
            # List only files in the current directory
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    result.append({
                        "filename": item,
                        "path": item,
                        "size": os.path.getsize(item_path),
                        "extension": os.path.splitext(item)[1].lower(),
                    })
    except Exception as e:
        print(f"Error scanning directory: {str(e)}")
        
    return result