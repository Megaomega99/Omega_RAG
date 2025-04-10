# worker/utils/file_utils.py
import os
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def get_file_path(filename: str, subdir: str = "") -> str:
    """
    Get absolute path for a file in the storage directory.
    
    Args:
        filename (str): Filename (without path)
        subdir (str, optional): Subdirectory within storage path
        
    Returns:
        str: Absolute file path
    """
    storage_path = settings.FILE_STORAGE_PATH
    if subdir:
        storage_path = os.path.join(storage_path, subdir)
        
    return os.path.join(storage_path, filename)

def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists.
    
    Args:
        directory (str): Directory path
    """
    os.makedirs(directory, exist_ok=True)

def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Hex digest of the hash
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
            
    return sha256.hexdigest()

def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)

def is_valid_file_type(filename: str) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if allowed, False otherwise
    """
    from shared.constants import ALLOWED_DOCUMENT_EXTENSIONS
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_DOCUMENT_EXTENSIONS

def get_embedding_path(document_id: int, chunk_id: int) -> str:
    """
    Get path for an embedding file.
    
    Args:
        document_id (int): Document ID
        chunk_id (int): Chunk ID
        
    Returns:
        str: Path to the embedding file
    """
    embeddings_dir = os.path.join(settings.FILE_STORAGE_PATH, "embeddings")
    ensure_directory(embeddings_dir)
    
    filename = f"doc_{document_id}_chunk_{chunk_id}.npy"
    return os.path.join(embeddings_dir, filename)

def save_embedding(
    document_id: int, 
    chunk_id: int, 
    embedding: List[float]
) -> str:
    """
    Save embedding to a file.
    
    Args:
        document_id (int): Document ID
        chunk_id (int): Chunk ID
        embedding (List[float]): Embedding vector
        
    Returns:
        str: Path to the embedding file (relative to storage path)
    """
    import numpy as np
    
    embedding_path = get_embedding_path(document_id, chunk_id)
    np.save(embedding_path, np.array(embedding))
    
    # Return path relative to storage path
    return os.path.relpath(embedding_path, settings.FILE_STORAGE_PATH)

def load_embedding(relative_path: str) -> Optional[List[float]]:
    """
    Load embedding from a file.
    
    Args:
        relative_path (str): Path relative to storage path
        
    Returns:
        Optional[List[float]]: Embedding vector or None if not found
    """
    import numpy as np
    
    full_path = os.path.join(settings.FILE_STORAGE_PATH, relative_path)
    
    if not os.path.exists(full_path):
        logger.warning(f"Embedding file not found: {full_path}")
        return None
        
    try:
        embedding = np.load(full_path)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error loading embedding {full_path}: {str(e)}")
        return None