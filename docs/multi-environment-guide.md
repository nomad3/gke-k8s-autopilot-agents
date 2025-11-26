# Multi-Environment Deployment Guide

This guide explains how to deploy and manage both dev and prod environments.

## Environment Strategy

### Dev Environment
- **Purpose**: Development, testing, experimentation
- **Cost**: Lower resources, fewer replicas
- **Stability**: RAPID/REGULAR release channel
- **Domains**: `dev-api.yourdomain.com`, `dev.yourdomain.com`
- **Secrets**: `dev-*` prefix in Secret Manager

### Prod Environment
- **Purpose**: Production workloads
- **Cost**: Higher resources, more replicas for HA
- **Stability**: REGULAR/STABLE release channel
- **Domains**: `api.yourdomain.com`, `yourdomain.com`
- **Secrets**: `prod-*` prefix in Secret Manager

## Infrastructure (Terraform)

### Deploy Dev Cluster

```bash
cd terraform/

# Copy and customize dev values
cp terraform.tfvars.example terraform-dev.tfvars
# Edit terraform-dev.tfvars with dev settings

# Deploy dev infrastructure
terraform workspace new dev  # Or: terraform workspace select dev
terraform apply -var-file="terraform-dev.tfvars"
```

### Deploy Prod Cluster

```bash
# Copy and customize prod values
cp terraform-prod.tfvars.example terraform-prod.tfvars
# Edit terraform-prod.tfvars with prod settings

# Deploy prod infrastructure
terraform workspace new prod  # Or: terraform workspace select prod
terraform apply -var-file="terraform-prod.tfvars"
```

### Separate State Per Environment

**Option 1: Terraform Workspaces**
```bash
terraform workspace list
terraform workspace select dev
terraform apply -var-file="terraform-dev.tfvars"

terraform workspace select prod
terraform apply -var-file="terraform-prod.tfvars"
```

**Option 2: Separate State Files (Recommended)**
```hcl
# backend-dev.tf
terraform {
  backend "gcs" {
    bucket = "PROJECT-terraform-state-dev"
    prefix = "gke-autopilot/state"
  }
}

# backend-prod.tf
terraform {
  backend "gcs" {
    bucket = "PROJECT-terraform-state-prod"
    prefix = "gke-autopilot/state"
  }
}
```

## Applications (Helm)

### Dev Deployment

```bash
# Get dev cluster credentials
gcloud container clusters get-credentials gke-autopilot-cluster-dev \
  --region us-central1 \
  --project PROJECT_ID_DEV

# Deploy to dev
helm upgrade --install backend \
  ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -n backend --create-namespace

helm upgrade --install frontend \
  ./helm/charts/microservice \
  -f ./helm/values/frontend-values.yaml \
  -n frontend --create-namespace

helm upgrade --install postgres \
  ./helm/charts/microservice \
  -f ./helm/values/database-values.yaml \
  -n database --create-namespace
```

### Prod Deployment

```bash
# Get prod cluster credentials
gcloud container clusters get-credentials gke-autopilot-cluster-prod \
  --region us-central1 \
  --project PROJECT_ID_PROD

# Deploy to prod with production values
helm upgrade --install backend \
  ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -f ./helm/values/backend-prod.yaml \
  -n backend --create-namespace

helm upgrade --install frontend \
  ./helm/charts/microservice \
  -f ./helm/values/frontend-values.yaml \
  -f ./helm/values/frontend-prod.yaml \
  -n frontend --create-namespace

helm upgrade --install postgres \
  ./helm/charts/microservice \
  -f ./helm/values/database-values.yaml \
  -f ./helm/values/database-prod.yaml \
  -n database --create-namespace
```

## Secret Manager (Per Environment)

### Dev Secrets

```bash
# Create dev secrets
gcloud secrets create dev-database-password --data-file=- <<< "dev_password"
gcloud secrets create dev-jwt-secret --data-file=- <<< "dev_jwt_secret_key"
gcloud secrets create dev-api-keys --data-file=- <<< '{"key": "dev_value"}'

# Grant access to dev backend SA
gcloud secrets add-iam-policy-binding dev-database-password \
  --member="serviceAccount:dev-backend-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Prod Secrets

```bash
# Create prod secrets (use strong values!)
gcloud secrets create prod-database-password --data-file=- <<< "STRONG_PROD_PASSWORD"
gcloud secrets create prod-jwt-secret --data-file=- <<< "STRONG_PROD_JWT_SECRET"
gcloud secrets create prod-api-keys --data-file=- <<< '{"key": "prod_value"}'

# Grant access to prod backend SA
gcloud secrets add-iam-policy-binding prod-database-password \
  --member="serviceAccount:prod-backend-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Key Differences: Dev vs Prod

| Aspect | Dev | Prod |
|--------|-----|------|
| **Replicas** | 2 min | 3+ min |
| **Autoscaling** | 2-10 | 3-20 |
| **Resources** | Lower (250m CPU) | Higher (500m+ CPU) |
| **Storage** | 50Gi HDD | 200Gi SSD |
| **Release Channel** | REGULAR | REGULAR/STABLE |
| **Image Tags** | `latest` | `v1.0.0` (specific) |
| **Log Level** | `debug` | `warn` |
| **Rate Limiting** | 50 rps | 100+ rps |
| **PDB minAvailable** | 1 | 2 |
| **Monitoring** | Basic | Enhanced |

## Cost Comparison

### Dev Environment
- GKE Autopilot: ~$60-80/month
- Cloud NAT: ~$25/month
- Load Balancer: $18/month
- Storage: ~$10/month
- **Total: ~$113-133/month**

### Prod Environment
- GKE Autopilot: ~$150-200/month (more resources)
- Cloud NAT: ~$40/month
- Load Balancer: $18/month
- Storage: ~$35/month (SSD)
- **Total: ~$243-293/month**

**Combined: ~$356-426/month**

## Promotion Strategy

### Promote Dev → Prod

```bash
# 1. Test in dev
helm test backend -n backend

# 2. Tag release
git tag v1.0.0
git push origin v1.0.0

# 3. Build and push prod image
docker build -t gcr.io/PROJECT_ID/backend:v1.0.0 .
docker push gcr.io/PROJECT_ID/backend:v1.0.0

# 4. Deploy to prod with specific tag
helm upgrade backend ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -f ./helm/values/backend-prod.yaml \
  --set image.tag=v1.0.0 \
  -n backend
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# Separate workflows per environment
.github/workflows/deploy-dev.yaml   # Deploys on push to main
.github/workflows/deploy-prod.yaml  # Deploys on tag creation

# Or environment-based
if: github.ref == 'refs/heads/main'
  # Deploy to dev
elif: startsWith(github.ref, 'refs/tags/v')
  # Deploy to prod
```

## Kubectl Context Management

```bash
# Save contexts with friendly names
kubectl config rename-context LONG_GKE_NAME dev-cluster
kubectl config rename-context LONG_GKE_NAME_PROD prod-cluster

# Switch between environments
kubectl config use-context dev-cluster
kubectl config use-context prod-cluster

# Or use kubectx (if installed)
kubectx dev-cluster
kubectx prod-cluster
```

## Best Practices

✅ **Never** deploy directly to prod - always test in dev first  
✅ **Always** use specific image tags in prod (not `latest`)  
✅ **Separate** GCP projects for dev and prod (recommended)  
✅ **Use** Terraform workspaces or separate state files  
✅ **Test** rollback procedures in dev before prod deployment  
✅ **Monitor** costs per environment with GCP labels  
✅ **Rotate** secrets regularly, especially in prod  
✅ **Document** all prod changes in change management system  
✅ **Back up** prod data before major updates  
✅ **Use** blue/green or canary deployments for prod

## Troubleshooting

### Wrong Environment Deployed

```bash
# Check current context
kubectl config current-context

# Verify namespace
kubectl get ns | grep -E "frontend|backend|database"

# Check pod labels
kubectl get pods -n backend -o jsonpath='{.items[0].metadata.labels.environment}'
```

### Secret Access Issues

```bash
# Verify ExternalSecret in correct namespace
kubectl get externalsecret -n backend

# Check Secret Manager IAM
gcloud secrets get-iam-policy prod-database-password
```

## Next Steps

1. Create separate GCP projects for dev and prod (recommended)
2. Deploy infrastructure to both environments
3. Set up environment-specific DNS records
4. Configure environment-specific secrets
5. Test dev deployment end-to-end
6. Establish promotion/deployment process
7. Set up environment-specific monitoring and alerts
