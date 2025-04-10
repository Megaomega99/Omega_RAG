# tests/backend/test_documents.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.document import Document

def test_get_empty_documents(client: TestClient, token_headers):
    """Test get documents when none exist."""
    response = client.get("/api/documents/", headers=token_headers)
    assert response.status_code == 200
    assert response.json() == []

def create_test_document(db: Session, owner_id: int) -> Document:
    """Create a test document in the database."""
    document = Document(
        title="Test Document",
        description="Test description",
        file_path="test_file.txt",
        file_type="txt",
        original_filename="test.txt",
        is_processed=True,
        is_indexed=True,
        processing_status="completed",
        owner_id=owner_id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def test_get_documents(client: TestClient, token_headers, db: Session, test_user):
    """Test get documents."""
    # Create a test document
    document = create_test_document(db, test_user["id"])
    
    # Get documents
    response = client.get("/api/documents/", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == document.id
    assert data[0]["title"] == document.title

def test_get_document_by_id(client: TestClient, token_headers, db: Session, test_user):
    """Test get document by ID."""
    # Create a test document
    document = create_test_document(db, test_user["id"])
    
    # Get document
    response = client.get(f"/api/documents/{document.id}", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document.id
    assert data["title"] == document.title

def test_get_document_not_found(client: TestClient, token_headers):
    """Test get document that doesn't exist."""
    response = client.get("/api/documents/999", headers=token_headers)
    assert response.status_code == 404
    assert "detail" in response.json()

def test_update_document(client: TestClient, token_headers, db: Session, test_user):
    """Test update document."""
    # Create a test document
    document = create_test_document(db, test_user["id"])
    
    # Update document
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = client.put(
        f"/api/documents/{document.id}", 
        json=update_data,
        headers=token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]

def test_delete_document(client: TestClient, token_headers, db: Session, test_user):
    """Test delete document."""
    # Create a test document
    document = create_test_document(db, test_user["id"])
    
    # Delete document
    response = client.delete(f"/api/documents/{document.id}", headers=token_headers)
    assert response.status_code == 200
    
    # Verify document is deleted
    doc_check = db.query(Document).filter(Document.id == document.id).first()
    assert doc_check is None