from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db import crud, models
from app.rag import embeddings, llm

router = APIRouter()

@router.post("/")
def ask_question(
    question: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Ask a question about documents and get an AI-generated answer."""
    # Generate embedding for the question
    question_embedding = embeddings.generate_embeddings([question])[0]
    
    # Get all document chunks
    all_chunks = db.query(models.DocumentChunk).all()
    
    # Find relevant chunks
    chunk_data = [
        {"id": chunk.id, "content": chunk.content, "embedding": chunk.embedding}
        for chunk in all_chunks
    ]
    relevant_chunks = embeddings.find_relevant_chunks(question_embedding, chunk_data)
    
    if not relevant_chunks:
        answer = "I couldn't find any relevant information in your documents to answer this question."
    else:
        # Generate response with RAG
        answer = llm.generate_rag_response(question, relevant_chunks)
    
    # Save the query
    query = crud.save_query(db, question, answer, current_user.id)
    
    return {
        "question": question,
        "answer": answer,
        "id": query.id
    }

@router.get("/history")
def get_query_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> List[Any]:
    """Get the user's query history."""
    queries = crud.get_user_queries(db, current_user.id, skip, limit)
    return [
        {
            "id": query.id,
            "question": query.question,
            "answer": query.answer,
            "created_at": query.created_at
        }
        for query in queries
    ]