FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend /app
COPY shared /app/shared

# Create directory for shared storage
RUN mkdir -p /app/shared_storage
COPY worker /app/worker

# Update PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH
# Add backend to PYTHONPATH for both containers
ENV PYTHONPATH=/app:/app/backend:$PYTHONPATH
# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]