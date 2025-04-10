FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY worker/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker /app/worker
COPY shared /app/shared

# Create directory for shared storage
RUN mkdir -p /app/shared_storage
# Add backend to PYTHONPATH for both containers
ENV PYTHONPATH=/app:/app/backend:$PYTHONPATH
# Set the working directory where Celery will run
WORKDIR /app

# Run Celery worker
CMD ["celery", "-A", "worker.main.celery", "worker", "--loglevel=info"]