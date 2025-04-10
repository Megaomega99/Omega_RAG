#!/bin/bash

# GCP Deployment Script for Omega RAG
# This script will deploy the Omega RAG application to Google Cloud Platform

# Exit on any error
set -e

# Configuration
PROJECT_ID=""           # Your GCP project ID
REGION="us-central1"    # GCP region
ZONE="us-central1-a"    # GCP zone
VM_NAME="omega-rag-vm"  # Name of the VM
VM_TYPE="e2-medium"     # VM machine type (2 vCPU, 4 GB RAM)
BOOT_DISK_SIZE="20GB"   # Boot disk size
DB_INSTANCE="omega-rag-db"  # Cloud SQL instance name
DB_NAME="omega_rag"     # Database name
DB_USER="omega_user"    # Database user
DB_PASSWORD=""          # Database password (will be generated if empty)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID is not set. Please edit this script and set it.${NC}"
    exit 1
fi

# Generate a random password if not set
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 12)
    echo -e "${YELLOW}Generated database password: ${DB_PASSWORD}${NC}"
    echo -e "${YELLOW}Please save this password for future use.${NC}"
fi

# Generate a random JWT secret key
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it before running this script.${NC}"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}You need to authenticate with Google Cloud.${NC}"
    gcloud auth login
fi

echo -e "${GREEN}Setting Google Cloud project to: ${PROJECT_ID}${NC}"
gcloud config set project $PROJECT_ID

# Ensure required APIs are enabled
echo -e "${GREEN}Enabling required Google Cloud APIs...${NC}"
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable servicenetworking.googleapis.com

# Create a VPC network for private IP
echo -e "${GREEN}Creating VPC network for private communication...${NC}"
gcloud compute networks create omega-rag-network --subnet-mode=auto || echo "Network already exists"

# Create a Cloud SQL instance
echo -e "${GREEN}Creating Cloud SQL instance (this may take several minutes)...${NC}"
gcloud sql instances create $DB_INSTANCE \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-size=10GB \
    --storage-type=SSD \
    --root-password=$DB_PASSWORD \
    --availability-type=ZONAL \
    --cpu=1 \
    --memory=614.4MB || echo "Cloud SQL instance already exists"

# Create database
echo -e "${GREEN}Creating database...${NC}"
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE || echo "Database already exists"

# Create database user
echo -e "${GREEN}Creating database user...${NC}"
gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password=$DB_PASSWORD || echo "User already exists"

# Get the database connection string
DB_IP=$(gcloud sql instances describe $DB_INSTANCE --format='value(ipAddresses.ipAddress)')
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_IP}:5432/${DB_NAME}"

# Create VM instance
echo -e "${GREEN}Creating VM instance...${NC}"
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=$VM_TYPE \
    --subnet=omega-rag-network \
    --boot-disk-size=$BOOT_DISK_SIZE \
    --boot-disk-type=pd-standard \
    --image-project=ubuntu-os-cloud \
    --image-family=ubuntu-2004-lts \
    --tags=http-server,https-server || echo "VM instance already exists"

# Configure firewall rules
echo -e "${GREEN}Configuring firewall rules...${NC}"
gcloud compute firewall-rules create allow-http \
    --network=omega-rag-network \
    --allow=tcp:80 \
    --target-tags=http-server || echo "HTTP firewall rule already exists"

gcloud compute firewall-rules create allow-https \
    --network=omega-rag-network \
    --allow=tcp:443 \
    --target-tags=https-server || echo "HTTPS firewall rule already exists"

# Get external IP of the VM
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='value(networkInterfaces[0].accessConfigs[0].natIP)')
echo -e "${GREEN}VM external IP: ${VM_IP}${NC}"

# Create .env file for Docker Compose
echo -e "${GREEN}Creating .env file for Docker Compose...${NC}"
cat > .env << EOF
DATABASE_URL=${DATABASE_URL}
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
GEMINI_API_KEY=your_gemini_api_key
EOF

echo -e "${YELLOW}Please update the GEMINI_API_KEY in the .env file with your actual API key.${NC}"

# Create setup script for VM
echo -e "${GREEN}Creating setup script for VM...${NC}"
cat > setup_vm.sh << EOF
#!/bin/bash
set -e

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker and Docker Compose
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-compose

# Add user to docker group
sudo usermod -aG docker \$USER

# Clone repository
git clone https://github.com/your-username/omega-rag.git
cd omega-rag

# Copy .env file
cat > .env << EOL
DATABASE_URL=${DATABASE_URL}
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
GEMINI_API_KEY=your_gemini_api_key
EOL

# Start containers
sudo docker-compose -f docker-compose.gcp.yml up -d

echo "Setup completed!"
EOF

chmod +x setup_vm.sh

# Copy files to VM
echo -e "${GREEN}Copying files to VM...${NC}"
gcloud compute scp setup_vm.sh .env ${VM_NAME}:~ --zone=$ZONE

# Show instructions
echo -e "${GREEN}===== Deployment Instructions =====${NC}"
echo -e "1. Connect to your VM: ${YELLOW}gcloud compute ssh ${VM_NAME} --zone=${ZONE}${NC}"
echo -e "2. Run the setup script: ${YELLOW}./setup_vm.sh${NC}"
echo -e "3. Update the Gemini API key in the .env file: ${YELLOW}nano .env${NC}"
echo -e "4. Restart the containers: ${YELLOW}cd omega-rag && sudo docker-compose -f docker-compose.gcp.yml up -d${NC}"
echo -e ""
echo -e "When completed, access your application at: ${YELLOW}http://${VM_IP}${NC}"
echo -e ""
echo -e "${GREEN}Database connection info:${NC}"
echo -e "Host: ${YELLOW}${DB_IP}${NC}"
echo -e "Port: ${YELLOW}5432${NC}"
echo -e "Database: ${YELLOW}${DB_NAME}${NC}"
echo -e "Username: ${YELLOW}${DB_USER}${NC}"
echo -e "Password: ${YELLOW}${DB_PASSWORD}${NC}"
echo -e ""
echo -e "${GREEN}===== Deployment Complete =====${NC}"