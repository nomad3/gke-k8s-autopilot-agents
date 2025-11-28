#!/bin/bash
set -e

# Script to enable required GCP APIs for GKE Autopilot infrastructure
# Usage: ./enable-gcp-apis.sh PROJECT_ID

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if project ID is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Project ID is required${NC}"
  echo "Usage: $0 PROJECT_ID"
  exit 1
fi

PROJECT_ID=$1

echo -e "${GREEN}Enabling GCP APIs for project: ${PROJECT_ID}${NC}"
echo "================================================"

# List of required APIs
APIS=(
  "compute.googleapis.com"
  "container.googleapis.com"
  "servicenetworking.googleapis.com"
  "containerregistry.googleapis.com"
  "artifactregistry.googleapis.com"
  "sql-component.googleapis.com"
  "sqladmin.googleapis.com"
  "secretmanager.googleapis.com"
  "iamcredentials.googleapis.com"
  "cloudresourcemanager.googleapis.com"
  "monitoring.googleapis.com"
  "logging.googleapis.com"
  "cloudbuild.googleapis.com"
  "binaryauthorization.googleapis.com"
)

# Set the project
echo -e "${YELLOW}Setting active project...${NC}"
gcloud config set project "${PROJECT_ID}"

# Enable APIs
echo -e "${YELLOW}Enabling APIs...${NC}"
for api in "${APIS[@]}"; do
  echo -e "  Enabling ${api}..."
  gcloud services enable "${api}" --project="${PROJECT_ID}"
done

echo ""
echo -e "${GREEN}✓ All APIs enabled successfully!${NC}"
echo ""
echo "Enabled APIs:"
for api in "${APIS[@]}"; do
  echo "  ✓ ${api}"
done

echo ""
echo -e "${GREEN}You can now run 'terraform apply'${NC}"
