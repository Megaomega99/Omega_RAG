# tests/worker/test_processing.py
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from worker.llm.text_processing import extract_text_from_document, chunk_text
from worker.llm.embedding import generate_embeddings
from worker.tasks.document_processing import process_document

def test_extract_text_from_txt():
    """Test extracting text from a .txt file."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        temp.write(b"This is a test document.\nWith multiple lines.")
        temp_path = temp.name
    
    try:
        # Extract text
        text = extract_text_from_document(temp_path, "txt")
        assert text == "This is a test document.\nWith multiple lines."
    finally:
        # Clean up
        os.unlink(temp_path)

def test_chunk_text():
    """Test text chunking."""
    # Test text with multiple paragraphs
    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3\n\nParagraph 4"
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    
    # Should split into chunks of appropriate size
    assert len(chunks) > 1
    
    # Test that each chunk is within the max size
    for chunk in chunks:
        assert len(chunk) <= 20

@patch('worker.llm.embedding.genai.embed_content')
def test_generate_embeddings(mock_embed_content):
    """Test generating embeddings."""
    # Mock the embedding model response
    mock_response = MagicMock()
    mock_response.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_embed_content.return_value = mock_response
    
    # Generate embeddings
    embeddings = generate_embeddings("Test text")
    
    # Verify result
    assert len(embeddings) == 5
    assert embeddings == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Verify the mock was called correctly
    mock_embed_content.assert_called_once()
    args, kwargs = mock_embed_content.call_args
    assert kwargs["content"] == "Test text"
    assert kwargs["task_type"] == "retrieval_document"

@patch('worker.tasks.document_processing.extract_text_from_document')
@patch('worker.tasks.document_processing.chunk_text')
@patch('worker.tasks.document_processing.generate_embeddings')
@patch('worker.tasks.document_processing.SessionLocal')
def test_process_document(
    mock_session_local, 
    mock_generate_embeddings, 
    mock_chunk_text, 
    mock_extract_text
):
    """Test document processing task."""
    # Mock database session and query results
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    # Mock document
    mock_document = MagicMock()
    mock_document.id = 1
    mock_document.file_path = "test.txt"
    mock_document.file_type = "txt"
    mock_db.query().filter().first.return_value = mock_document
    
    # Mock path existence
    with patch('os.path.exists', return_value=True):
        # Mock extract text
        mock_extract_text.return_value = "Test document content"
        
        # Mock chunk text
        mock_chunk_text.return_value = ["Chunk 1", "Chunk 2"]
        
        # Mock embeddings
        mock_generate_embeddings.return_value = [0.1, 0.2, 0.3]
        
        # Mock file operations
        with patch('os.makedirs'):
            with patch('numpy.save'):
                # Call the task
                result = process_document(1)
                
                # Verify result
                assert result["success"] is True
                assert result["document_id"] == 1
                assert result["chunks_count"] == 2
                
                # Verify document was updated
                assert mock_document.is_processed is True
                assert mock_document.is_indexed is True
                assert mock_document.processing_status == "completed"
                
                # Verify DB was committed
                assert mock_db.commit.called