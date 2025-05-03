#!/bin/bash
# Cloud SQL PostgreSQL setup for RAG SaaS application

# Prerequisites: 
# 1. gcloud CLI installed and authenticated
# 2. Replace variables below with your actual values

# Variables
PROJECT_ID="your-project-id"  # Your GCP project ID
INSTANCE_NAME="rag-saas-db"    # Cloud SQL instance name
REGION="us-central1"           # Same region as your GCP instances
DB_VERSION="POSTGRES_14"       # PostgreSQL version
TIER="db-g1-small"             # Machine type
DB_NAME="rag_saas"             # Database name
DB_USER="postgres"             # Database user
DB_PASSWORD="your_db_password" # Database password - use a strong password!

# Create Cloud SQL PostgreSQL instance
echo "Creating Cloud SQL PostgreSQL instance..."
gcloud sql instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --database-version=$DB_VERSION \
    --tier=$TIER \
    --region=$REGION \
    --storage-size=10GB \
    --storage-type=SSD \
    --availability-type=ZONAL \
    --root-password=$DB_PASSWORD

# Create database
echo "Creating database..."
gcloud sql databases create $DB_NAME \
    --instance=$INSTANCE_NAME \
    --project=$PROJECT_ID

# Create user if different from default postgres user
if [ "$DB_USER" != "postgres" ]; then
    echo "Creating database user..."
    gcloud sql users create $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$DB_PASSWORD \
        --project=$PROJECT_ID
fi

# Configure network
echo "Configuring network access..."

# Add authorized networks for your GCP instances
# It's better to use Private IP with VPC peering for production
gcloud sql instances patch $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --authorized-networks=10.128.0.8/32,10.128.0.9/32,10.128.0.10/32

echo "Cloud SQL PostgreSQL instance setup complete!"
echo "Connection details:"
echo "Instance connection name: $PROJECT_ID:$REGION:$INSTANCE_NAME"
echo "Database name: $DB_NAME"
echo "Username: $DB_USER"

# Note: For production environments, consider:
# 1. Using Private IP with VPC peering instead of authorized networks
# 2. Enabling backup and high availability
# 3. Setting up SSL certificates for secure connections
