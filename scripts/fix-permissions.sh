#!/bin/bash
set -e

# Usage: ./fix-permissions.sh <PROJECT_ID> <SERVICE_ACCOUNT_EMAIL>

PROJECT_ID=$1
SA_EMAIL=$2

if [ -z "$PROJECT_ID" ] || [ -z "$SA_EMAIL" ]; then
  echo "Usage: $0 <PROJECT_ID> <SERVICE_ACCOUNT_EMAIL>"
  exit 1
fi

echo "Granting roles to $SA_EMAIL in project $PROJECT_ID..."

ROLES=(
  "roles/iam.serviceAccountAdmin"
  "roles/storage.admin"
  "roles/artifactregistry.admin"
  "roles/secretmanager.admin"
  "roles/resourcemanager.projectIamAdmin"
  "roles/container.admin"
  "roles/compute.networkAdmin"
)

for role in "${ROLES[@]}"; do
  echo "Granting $role..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$role"
done

echo "Permissions granted successfully."
