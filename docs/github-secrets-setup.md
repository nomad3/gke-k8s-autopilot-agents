# GitHub Secrets Setup Guide for Terraform CI/CD

This guide walks you through setting up the required GitHub Secrets for automated Terraform deployments to GCP.

## Prerequisites

- GCP CLI (`gcloud`) installed and authenticated
- Owner or Editor role on your GCP projects
- Admin access to your GitHub repository

## Required Secrets

### Development Environment
- `GCP_PROJECT_ID_DEV` - GCP Project ID
- `GCP_SA_KEY_DEV` - Service Account JSON key
- `GCS_BUCKET_DEV` - Terraform state bucket name

### Production Environment
- `GCP_PROJECT_ID_PROD` - GCP Project ID
- `GCP_SA_KEY_PROD` - Service Account JSON key
- `GCS_BUCKET_PROD` - Terraform state bucket name

---

## Step 1: Create GCS Buckets for Terraform State

### Development Bucket
```bash
# Set your dev project ID
export DEV_PROJECT_ID="your-dev-project-id"

# Create the bucket
gcloud storage buckets create gs://${DEV_PROJECT_ID}-terraform-state \
  --project=${DEV_PROJECT_ID} \
  --location=US \
  --uniform-bucket-level-access

# Enable versioning (for state recovery)
gcloud storage buckets update gs://${DEV_PROJECT_ID}-terraform-state \
  --versioning
```

### Production Bucket
```bash
# Set your prod project ID
export PROD_PROJECT_ID="your-prod-project-id"

# Create the bucket
gcloud storage buckets create gs://${PROD_PROJECT_ID}-terraform-state \
  --project=${PROD_PROJECT_ID} \
  --location=US \
  --uniform-bucket-level-access

# Enable versioning
gcloud storage buckets update gs://${PROD_PROJECT_ID}-terraform-state \
  --versioning
```

---

## Step 2: Create Service Accounts

### Development Service Account
```bash
# Create service account
gcloud iam service-accounts create terraform-cicd-dev \
  --display-name="Terraform CI/CD - Development" \
  --project=${DEV_PROJECT_ID}

# Grant necessary roles
gcloud projects add-iam-policy-binding ${DEV_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-dev@${DEV_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding ${DEV_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-dev@${DEV_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

gcloud projects add-iam-policy-binding ${DEV_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-dev@${DEV_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"
```

### Production Service Account
```bash
# Create service account
gcloud iam service-accounts create terraform-cicd-prod \
  --display-name="Terraform CI/CD - Production" \
  --project=${PROD_PROJECT_ID}

# Grant necessary roles
gcloud projects add-iam-policy-binding ${PROD_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-prod@${PROD_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding ${PROD_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-prod@${PROD_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

gcloud projects add-iam-policy-binding ${PROD_PROJECT_ID} \
  --member="serviceAccount:terraform-cicd-prod@${PROD_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"
```

---

## Step 3: Create and Download Service Account Keys

### Development Key
```bash
gcloud iam service-accounts keys create ~/terraform-dev-key.json \
  --iam-account=terraform-cicd-dev@${DEV_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${DEV_PROJECT_ID}

# Display the key (copy this for GitHub)
cat ~/terraform-dev-key.json
```

### Production Key
```bash
gcloud iam service-accounts keys create ~/terraform-prod-key.json \
  --iam-account=terraform-cicd-prod@${PROD_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${PROD_PROJECT_ID}

# Display the key (copy this for GitHub)
cat ~/terraform-prod-key.json
```

> **⚠️ SECURITY WARNING**: These keys grant significant permissions. Store them securely and delete the local files after adding to GitHub.

---

## Step 4: Add Secrets to GitHub

1. **Navigate to your repository** on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

### Development Secrets

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID_DEV` | Your dev project ID (e.g., `my-project-dev`) |
| `GCP_SA_KEY_DEV` | Entire contents of `terraform-dev-key.json` |
| `GCS_BUCKET_DEV` | Bucket name (e.g., `my-project-dev-terraform-state`) |

### Production Secrets

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID_PROD` | Your prod project ID (e.g., `my-project-prod`) |
| `GCP_SA_KEY_PROD` | Entire contents of `terraform-prod-key.json` |
| `GCS_BUCKET_PROD` | Bucket name (e.g., `my-project-prod-terraform-state`) |

---

## Step 5: Clean Up Local Key Files

```bash
# Securely delete the key files
rm ~/terraform-dev-key.json
rm ~/terraform-prod-key.json
```

---

## Step 6: Enable Required GCP APIs

Both projects need these APIs enabled:

```bash
# For Dev
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  --project=${DEV_PROJECT_ID}

# For Prod
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  --project=${PROD_PROJECT_ID}
```

---

## Verification

### Test Dev Workflow
```bash
# Push to main branch (triggers dev deployment)
git push origin main
```

### Test Prod Workflow
```bash
# Create and push a tag (triggers prod deployment)
git tag infra-v1.0.0
git push origin infra-v1.0.0
```

Or use **workflow_dispatch** from GitHub Actions UI.

---

## Troubleshooting

### "Permission Denied" Errors
- Verify the service account has all required roles
- Check that APIs are enabled in the project

### "Bucket Not Found" Errors
- Verify the bucket name in GitHub secrets matches the actual bucket
- Ensure the service account has access to the bucket

### "Backend Initialization Failed"
- Verify the `prefix` is specified in the workflow or use Terraform workspaces
- Check that the bucket exists and versioning is enabled

---

## Security Best Practices

1. **Rotate keys regularly** (every 90 days)
2. **Use separate projects** for dev and prod
3. **Enable audit logging** on service accounts
4. **Review IAM permissions** periodically
5. **Never commit** `.tfvars` or service account keys to Git

---

## Next Steps

After secrets are configured:
1. Update `terraform-dev.tfvars` and `terraform-prod.tfvars` locally
2. Test locally with `terraform plan`
3. Push changes to trigger automated deployments
