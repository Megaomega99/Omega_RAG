#!/bin/bash
# Setup script for web-server instance (FastAPI backend)

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-venv nginx postgresql-client

# Create app directory
mkdir -p /opt/rag-saas
cd /opt/rag-saas

# Clone repository (replace with your repository)
git clone https://github.com/Megaomega99/Omega_RAG.git .

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn google-cloud-storage pg8000==1.29.0

# Install Cloud SQL Auth Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.0.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/

# Create systemd service for Cloud SQL Auth Proxy
cat > /tmp/cloud-sql-proxy.service << 'EOF'
[Unit]
Description=Cloud SQL Auth Proxy
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port 5432 INSTANCE_CONNECTION_NAME
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Replace INSTANCE_CONNECTION_NAME with actual value
# Example: my-project:us-central1:my-instance
sed -i 's/INSTANCE_CONNECTION_NAME/your-project-id:us-central1:rag-saas-db/g' /tmp/cloud-sql-proxy.service
sudo mv /tmp/cloud-sql-proxy.service /etc/systemd/system/

# Create .env file for application
cat > .env << 'EOF'
SECRET_KEY=your-secure-secret-key-here
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_NAME=rag_saas
DB_INSTANCE_CONNECTION_NAME=your-project-id:us-central1:rag-saas-db
USE_CLOUD_SQL_AUTH_PROXY=True

FILE_SERVER_INTERNAL_IP=10.128.0.8
FILE_SERVER_EXTERNAL_IP=35.232.252.195
WEB_SERVER_INTERNAL_IP=10.128.0.9
WORKER_INTERNAL_IP=10.128.0.10

UPLOAD_FOLDER=/mnt/filestore
OLLAMA_BASE_URL=http://10.128.0.10:11434
OLLAMA_MODEL=tinyllama
EOF

# Create systemd service for API
cat > /tmp/rag-saas-api.service << 'EOF'
[Unit]
Description=RAG SaaS API Service
After=network.target cloud-sql-proxy.service

[Service]
User=root
WorkingDirectory=/opt/rag-saas
ExecStart=/opt/rag-saas/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
Restart=always
RestartSec=3
Environment=PYTHONPATH=/opt/rag-saas
EnvironmentFile=/opt/rag-saas/.env

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/rag-saas-api.service /etc/systemd/system/

# Configure Nginx as reverse proxy
cat > /tmp/rag-saas.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo mv /tmp/rag-saas.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/rag-saas.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create filestore mount point
sudo mkdir -p /mnt/filestore

# Start services
sudo systemctl daemon-reload
sudo systemctl enable cloud-sql-proxy.service
sudo systemctl enable rag-saas-api.service
sudo systemctl enable nginx

sudo systemctl start cloud-sql-proxy.service
sudo systemctl start rag-saas-api.service
sudo systemctl restart nginx

echo "Web server setup complete!"
