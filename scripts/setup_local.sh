#!/bin/bash
# scripts/setup_local.sh

# Setup script for local development environment
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    
    # Generate JWT secret key
    JWT_SECRET=$(openssl rand -base64 32)
    
    cat > .env << EOF
# PostgreSQL Database Configuration
POSTGRES_USER=omega_user
POSTGRES_PASSWORD=omega_password
POSTGRES_DB=omega_rag
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# JWT Authentication
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# File Storage
FILE_STORAGE_PATH=/app/shared_storage

# Google Gemini API
GEMINI_API_KEY=

# Environment Configuration
ENVIRONMENT=development
EOF

    echo -e "${YELLOW}Please set your Google Gemini API key in the .env file.${NC}"
    echo -e "${YELLOW}Get it from: https://makersuite.google.com/app/apikey${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Create shared_storage directory
mkdir -p shared_storage

# Build and start the containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo -e "${GREEN}Waiting for database to be ready...${NC}"
sleep 10

# Initialize the database
echo -e "${GREEN}Initializing the database...${NC}"
docker-compose exec backend alembic upgrade head

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}Access the application at:${NC}"
echo -e "  - Frontend: http://localhost:80"
echo -e "  - Backend API: http://localhost:80/api"
echo -e "  - API Documentation: http://localhost:80/api/docs"