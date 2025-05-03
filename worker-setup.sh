#!/bin/bash
# Setup script for worker instance (Ollama LLM service)

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y curl nfs-common

# Mount shared file storage from file-server
sudo mkdir -p /mnt/filestore
sudo mount 10.128.0.8:/mnt/filestore /mnt/filestore

# Add mount entry to fstab for persistence across reboots
echo "10.128.0.8:/mnt/filestore /mnt/filestore nfs defaults 0 0" | sudo tee -a /etc/fstab

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create systemd service for Ollama
cat > /tmp/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/ollama.service /etc/systemd/system/

# Pull the required model
cat > /tmp/pull-model.service << 'EOF'
[Unit]
Description=Pull Ollama Model
After=ollama.service
Requires=ollama.service

[Service]
Type=oneshot
User=root
ExecStart=/usr/local/bin/ollama pull tinyllama
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/pull-model.service /etc/systemd/system/

# Start services
sudo systemctl daemon-reload
sudo systemctl enable ollama.service
sudo systemctl enable pull-model.service

sudo systemctl start ollama.service
sudo systemctl start pull-model.service

# Set firewall rules to allow Ollama API port
sudo apt-get install -y ufw
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 11434/tcp  # Ollama API
sudo ufw enable

echo "Worker node setup complete!"
