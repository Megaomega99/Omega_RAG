# RAG SaaS Application

A Retrieval-Augmented Generation (RAG) Software-as-a-Service application that enables users to upload documents, process them with AI, and query them using natural language.

## Features

- Upload PDF, TXT, DOCX, and Markdown documents
- Automatic text extraction and chunking
- Vector embeddings for semantic search
- Natural language querying with AI-generated responses
- User authentication and document management
- Simple, minimal frontend interface for testing

## Requirements

- Docker and Docker Compose
- At least 4GB of RAM (for Ollama model)

## Getting Started

1. Clone the repository: https://github.com/Megaomega99/rag-saas.git
2. Start the application with Docker Compose: docker-compose up -d
3. Access the application:
- Frontend UI: http://localhost:7000
- API documentation: http://localhost:8000/docs

## Usage

1. Register for an account or login
2. Upload documents in the Documents tab
3. Wait for the documents to be processed
4. Ask questions about your documents in the Ask Questions tab

## Architecture

- FastAPI backend with PostgreSQL database
- Vector embeddings for document retrieval
- Ollama integration for lightweight LLM processing
- Flet-based minimal frontend UI
- Containerized deployment with Docker

## Development

To run the application in development mode:

1. Create a virtual environment: python -m venv venv source venv/bin/activate  # On Windows: venv\Scripts\activate
2. Install dependencies: pip install -r requirements.txt
3. Start PostgreSQL and Ollama in Docker: docker-compose up -d db ollama
4. Run the FastAPI application: uvicorn app.main --reload
5. Run the frontend in a separate terminal: python -m app.frontend.main
