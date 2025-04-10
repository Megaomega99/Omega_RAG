# Omega_RAG: RAG SaaS Application

Omega_RAG is a sophisticated Retrieval Augmented Generation (RAG) SaaS application that enables users to efficiently process, analyze, and query documents using state-of-the-art AI technologies. The system utilizes Google's Gemini API for language model capabilities, integrating them with a robust document processing pipeline.

## Architecture Overview

Omega_RAG implements a modular, scalable architecture with the following components:

- **Backend API**: FastAPI-based REST API server handling document management, user authentication, and RAG queries
- **Worker Service**: Asynchronous document processing using Celery for text extraction, chunking, and embedding generation
- **Frontend UI**: Flet-based responsive interface for document management and conversational AI interaction
- **Data Storage**: PostgreSQL database for structured data and file system for document storage
- **Vector Indexing**: Similarity-based retrieval using embeddings for context-aware answers

### Technical Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic, JWT
- **Worker**: Celery, Redis, Google Generative AI SDK, LangChain
- **Frontend**: Flet (Python-based UI framework)
- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Deployment**: Nginx, Gunicorn, Google Cloud Platform

## Local Development Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL (optional if using Docker)
- Redis (optional if using Docker)
- Google Cloud Gemini API key

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/omega_rag.git
   cd omega_rag
   ```

2. Create a `.env` file in the project root:
   ```
   POSTGRES_USER=omega_user
   POSTGRES_PASSWORD=omega_password
   POSTGRES_DB=omega_rag
   POSTGRES_SERVER=postgres
   POSTGRES_PORT=5432
   
   REDIS_HOST=redis
   REDIS_PORT=6379
   
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   
   GEMINI_API_KEY=your-gemini-api-key
   ```

3. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```

4. Initialize the database (if needed):
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. Access the application:
   - Frontend: http://localhost:80
   - Backend API: http://localhost:80/api
   - API Documentation: http://localhost:80/api/docs

## Key Features

- **Document Processing**: Upload and process PDF, TXT, DOCX, and Markdown documents
- **Text Analysis**: Automatic text extraction, chunking, and embedding generation
- **Conversational AI**: Chat with your documents using natural language queries
- **Context-Aware Responses**: Responses are generated based on document content with source attribution
- **User Management**: Secure authentication and user-specific document management

## Project Structure

The project follows a modular structure:

```
omega_rag/
├── backend/            # FastAPI application
│   ├── app/            # API implementation
│   ├── alembic/        # Database migrations
│   └── requirements.txt
├── worker/             # Celery worker implementation
│   ├── tasks/          # Async processing tasks
│   ├── llm/            # LLM integration modules
│   └── requirements.txt
├── frontend/           # Flet UI application
│   ├── pages/          # UI page components
│   ├── components/     # Reusable UI components
│   └── requirements.txt
├── docker/             # Docker configuration
│   ├── backend/        # Backend Dockerfile
│   ├── worker/         # Worker Dockerfile
│   ├── frontend/       # Frontend Dockerfile
│   └── nginx/          # Nginx configuration
├── scripts/            # Deployment and utility scripts
├── docker-compose.yml  # Local development configuration
└── docker-compose.gcp.yml # GCP deployment configuration
```

## API Documentation

The backend API provides the following endpoints:

- **Authentication**:
  - `POST /api/auth/login`: Obtain JWT token
  - `POST /api/auth/register`: Register new user
  - `GET /api/auth/me`: Get current user information

- **Documents**:
  - `GET /api/documents`: List user documents
  - `POST /api/documents`: Upload new document
  - `GET /api/documents/{document_id}`: Get document details
  - `PUT /api/documents/{document_id}`: Update document metadata
  - `DELETE /api/documents/{document_id}`: Delete document

- **RAG Interaction**:
  - `POST /api/rag/query`: Submit RAG query
  - `GET /api/rag/conversations`: List conversations
  - `GET /api/rag/conversations/{conversation_id}`: Get conversation details

## GCP Deployment

### Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Google Cloud SQL instance (PostgreSQL)
- Google Cloud Compute Engine VM instances
- Google Cloud Gemini API key

### Deployment Steps

1. Update the `scripts/deploy_gcp.sh` script with your GCP project details:
   ```bash
   # Edit PROJECT_ID and other configuration variables
   nano scripts/deploy_gcp.sh
   ```

2. Run the deployment script:
   ```bash
   chmod +x scripts/deploy_gcp.sh
   ./scripts/deploy_gcp.sh
   ```

3. Follow the instructions provided by the script to complete the setup on your VM instances.

4. Configure the Nginx reverse proxy to serve the application.

The deployment architecture includes:
- 1 VM for Web Server (Nginx + Backend API)
- 1 VM for Worker
- 1 VM for File Server (NFS)
- 1 Cloud SQL instance for PostgreSQL

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.