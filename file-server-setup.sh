#!/bin/bash
# Setup script for file-server instance (File storage and frontend)

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-venv nginx nfs-kernel-server

# Create app directory
mkdir -p /opt/rag-saas
cd /opt/rag-saas

# Clone repository
git clone https://github.com/Megaomega99/Omega_RAG.git .

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create file storage directory
sudo mkdir -p /mnt/filestore
sudo chown -R nobody:nogroup /mnt/filestore
sudo chmod 777 /mnt/filestore

# Configure NFS server to share file storage
echo "/mnt/filestore 10.128.0.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# Create .env file for frontend
cat > .env << 'EOF'
API_BASE_URL=http://10.128.0.9:8000/api/v1
EOF

# Create systemd service for frontend
cat > /tmp/rag-saas-frontend.service << 'EOF'
[Unit]
Description=RAG SaaS Frontend Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/rag-saas
ExecStart=/opt/rag-saas/venv/bin/python -m app.frontend.main
Restart=always
RestartSec=3
Environment=PYTHONPATH=/opt/rag-saas
EnvironmentFile=/opt/rag-saas/.env

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/rag-saas-frontend.service /etc/systemd/system/

# Configure Nginx as reverse proxy for frontend
cat > /tmp/rag-saas-frontend.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo mv /tmp/rag-saas-frontend.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/rag-saas-frontend.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl enable rag-saas-frontend.service
sudo systemctl enable nginx

sudo systemctl start rag-saas-frontend.service
sudo systemctl restart nginx

# Set firewall rules to allow Flet frontend port
sudo apt-get install -y ufw
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 7000/tcp  # Flet
sudo ufw allow 2049/tcp  # NFS
sudo ufw enable

echo "File server setup complete!"
