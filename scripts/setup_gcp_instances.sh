#!/bin/bash

# GCP Instance Configuration Script for Omega RAG
# This script configures the three VM instances required for the application architecture

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
WEB_SERVER_NAME="omega-rag-web"     # Web Server VM name
WORKER_NAME="omega-rag-worker"      # Worker VM name
FILE_SERVER_NAME="omega-rag-nfs"    # File Server VM name
ZONE="us-central1-a"                # GCP zone

# Functions
function configure_web_server() {
    echo -e "${GREEN}Configuring Web Server VM (${WEB_SERVER_NAME})...${NC}"
    
    # Connect to the VM and execute the setup commands
    gcloud compute ssh ${WEB_SERVER_NAME} --zone=${ZONE} --command="
        # Update system
        sudo apt-get update
        sudo apt-get upgrade -y
        
        # Install Docker and Docker Compose
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\"
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-compose
        
        # Add user to docker group
        sudo usermod -aG docker \$USER
        
        # Install Nginx
        sudo apt-get install -y nginx
        
        # Configure Nginx
        sudo tee /etc/nginx/sites-available/omega-rag << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:7777;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # For file uploads
        client_max_body_size 50M;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
        
        # Enable the site
        sudo ln -sf /etc/nginx/sites-available/omega-rag /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        
        # Test Nginx configuration
        sudo nginx -t
        
        # Restart Nginx
        sudo systemctl restart nginx
        
        # Create NFS mount directory
        sudo mkdir -p /mnt/nfs
        
        # Install NFS client
        sudo apt-get install -y nfs-common
        
        echo 'Setup of Web Server completed!'
    "
    
    echo -e "${GREEN}Web Server configuration completed!${NC}"
}

function configure_worker() {
    echo -e "${GREEN}Configuring Worker VM (${WORKER_NAME})...${NC}"
    
    # Connect to the VM and execute the setup commands
    gcloud compute ssh ${WORKER_NAME} --zone=${ZONE} --command="
        # Update system
        sudo apt-get update
        sudo apt-get upgrade -y
        
        # Install Docker and Docker Compose
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\"
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-compose
        
        # Add user to docker group
        sudo usermod -aG docker \$USER
        
        # Create NFS mount directory
        sudo mkdir -p /mnt/nfs
        
        # Install NFS client
        sudo apt-get install -y nfs-common
        
        echo 'Setup of Worker VM completed!'
    "
    
    echo -e "${GREEN}Worker configuration completed!${NC}"
}

function configure_file_server() {
    echo -e "${GREEN}Configuring File Server VM (${FILE_SERVER_NAME})...${NC}"
    
    # Connect to the VM and execute the setup commands
    gcloud compute ssh ${FILE_SERVER_NAME} --zone=${ZONE} --command="
        # Update system
        sudo apt-get update
        sudo apt-get upgrade -y
        
        # Create NFS directory
        sudo mkdir -p /var/nfs/omega_rag
        sudo chown nobody:nogroup /var/nfs/omega_rag
        sudo chmod 777 /var/nfs/omega_rag
        
        # Install NFS server
        sudo apt-get install -y nfs-kernel-server
        
        # Configure NFS exports
        echo '/var/nfs/omega_rag *(rw,sync,no_subtree_check,no_root_squash)' | sudo tee -a /etc/exports
        
        # Apply the NFS configuration
        sudo exportfs -a
        sudo systemctl restart nfs-kernel-server
        
        echo 'Setup of File Server completed!'
    "
    
    echo -e "${GREEN}File Server configuration completed!${NC}"
}

function mount_nfs() {
    # Get File Server internal IP
    FILE_SERVER_IP=$(gcloud compute instances describe ${FILE_SERVER_NAME} --zone=${ZONE} --format='value(networkInterfaces[0].networkIP)')
    
    echo -e "${GREEN}Mounting NFS from ${FILE_SERVER_IP} to Web Server and Worker...${NC}"
    
    # Mount NFS on Web Server
    gcloud compute ssh ${WEB_SERVER_NAME} --zone=${ZONE} --command="
        # Mount NFS
        echo '${FILE_SERVER_IP}:/var/nfs/omega_rag /mnt/nfs nfs defaults 0 0' | sudo tee -a /etc/fstab
        sudo mount -a
        
        # Verify mount
        df -h | grep nfs
    "
    
    # Mount NFS on Worker
    gcloud compute ssh ${WORKER_NAME} --zone=${ZONE} --command="
        # Mount NFS
        echo '${FILE_SERVER_IP}:/var/nfs/omega_rag /mnt/nfs nfs defaults 0 0' | sudo tee -a /etc/fstab
        sudo mount -a
        
        # Verify mount
        df -h | grep nfs
    "
    
    echo -e "${GREEN}NFS mount completed!${NC}"
}

# Main execution
echo -e "${GREEN}======= Setting Up Omega RAG Instances =======${NC}"

# Check if required VMs exist
if ! gcloud compute instances describe ${WEB_SERVER_NAME} --zone=${ZONE} &> /dev/null; then
    echo -e "${RED}Error: Web Server VM (${WEB_SERVER_NAME}) not found.${NC}"
    exit 1
fi

if ! gcloud compute instances describe ${WORKER_NAME} --zone=${ZONE} &> /dev/null; then
    echo -e "${RED}Error: Worker VM (${WORKER_NAME}) not found.${NC}"
    exit 1
fi

if ! gcloud compute instances describe ${FILE_SERVER_NAME} --zone=${ZONE} &> /dev/null; then
    echo -e "${RED}Error: File Server VM (${FILE_SERVER_NAME}) not found.${NC}"
    exit 1
fi

# Configure all instances
configure_file_server
configure_web_server
configure_worker
mount_nfs

echo -e "${GREEN}======= All instances configured successfully! =======${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Deploy the application using the deploy_gcp.sh script"
echo -e "2. Configure environment variables on each instance"
echo -e "3. Start the application containers"
echo -e ""