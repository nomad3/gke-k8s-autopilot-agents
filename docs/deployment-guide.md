# Stage-by-Stage Deployment Guide

Follow these steps in order to deploy your GKE Autopilot infrastructure and applications.

## Prerequisites ✅

- [x] GitHub secrets configured
- [ ] GCS bucket created for Terraform state
- [ ] Domain name ready (if using DNS module)

---

## Stage 1: Deploy Infrastructure (Terraform)

### Step 1.1: Create GCS Bucket for Terraform State

Run this **once** in your local terminal:

```bash
export PROJECT_ID="your-gcp-project-id-dev"

gcloud storage buckets create gs://${PROJECT_ID}-terraform-state \
  --project=${PROJECT_ID} \
  --location=US \
  --uniform-bucket-level-access

# Enable versioning
gcloud storage buckets update gs://${PROJECT_ID}-terraform-state --versioning
```

### Step 1.2: Update Terraform Variables

Edit `terraform/terraform-dev.tfvars` with your actual values:
- Project ID
- Domain name (if using DNS)
- DNS records (if using DNS)

### Step 1.3: Commit and Push Changes

```bash
git add .
git commit -m "Configure Terraform for dev environment"
git push origin main
```

### Step 1.4: Deploy Infrastructure via GitHub Actions

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Terraform** workflow
4. Click **Run workflow**
5. Select:
   - Environment: `dev`
   - Action: `plan`
6. Click **Run workflow**
7. **Review the plan output** carefully
8. If plan looks good, run again with:
   - Environment: `dev`
   - Action: `apply`

**Wait for completion** (~10-15 minutes)

### Step 1.5: Verify Infrastructure

Check the workflow output for:
- ✅ Cluster created
- ✅ VPC and networking configured
- ✅ Database created
- ✅ DNS zone created (if enabled)

---

## Stage 2: Connect to Cluster

Run this in your **local terminal**:

```bash
# Get cluster credentials
gcloud container clusters get-credentials gke-autopilot-cluster-dev \
  --region us-central1 \
  --project your-project-id-dev

# Verify connection
kubectl get nodes
kubectl cluster-info
```

You should see nodes listed (may take a few minutes for nodes to appear).

---

## Stage 3: Deploy Kubernetes Infrastructure

### Step 3.1: Deploy via GitHub Actions

1. Go to **Actions** tab
2. Select **Kubernetes Infrastructure** workflow
3. Click **Run workflow**
4. Select environment: `dev`
5. Click **Run workflow**

**Wait for completion** (~2-5 minutes)

### Step 3.2: Verify Gateway

Check the workflow summary for the Gateway IP address, or run:

```bash
# Check Gateway status
kubectl get gateway -n gateway-system

# Get Gateway IP
kubectl get gateway external-gateway -n gateway-system \
  -o jsonpath='{.status.addresses[0].value}'
```

**Save this IP address** - you'll need it for DNS.

### Step 3.3: Verify Namespaces

```bash
kubectl get namespaces
```

You should see:
- `gateway-system`
- `backend`
- `frontend`

---

## Stage 4: Configure DNS

### Option A: If Using Terraform DNS Module

1. Get nameservers:
```bash
cd terraform
terraform output dns_name_servers
```

2. Update your domain registrar:
   - Go to your domain registrar (e.g., GoDaddy, Namecheap, Google Domains)
   - Update nameservers to the ones from Terraform output
   - Wait 24-48 hours for propagation

### Option B: Manual DNS Configuration

Point your domain to the Gateway IP from Stage 3.2:

**A Records to create:**
- `api.yourdomain.com` → Gateway IP
- `www.yourdomain.com` → Gateway IP
- `yourdomain.com` → Gateway IP

---

## Stage 5: Deploy Applications

### Step 5.1: Build and Push Images (First Time)

If you don't have Docker images yet, you need to build them first.

**Option 1: Via GitHub Actions (Recommended)**

Push your application code:
```bash
git add backend/ frontend/
git commit -m "Add application code"
git push origin main
```

This will trigger `backend-dev.yaml` and `frontend-dev.yaml` workflows.

**Option 2: Build Locally**

```bash
# Authenticate Docker
gcloud auth configure-docker

# Build and push backend
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/backend:dev-latest .
docker push gcr.io/YOUR_PROJECT_ID/backend:dev-latest

# Build and push frontend
cd ../frontend
docker build -t gcr.io/YOUR_PROJECT_ID/frontend:dev-latest .
docker push gcr.io/YOUR_PROJECT_ID/frontend:dev-latest
```

### Step 5.2: Deploy Applications

The GitHub Actions workflows will automatically deploy after building images.

Or deploy manually with Helm:

```bash
# Deploy backend
helm upgrade --install backend ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -n backend --create-namespace --wait

# Deploy frontend
helm upgrade --install frontend ./helm/charts/microservice \
  -f ./helm/values/frontend-values.yaml \
  -n frontend --create-namespace --wait
```

### Step 5.3: Verify Deployments

```bash
# Check pods
kubectl get pods -n backend
kubectl get pods -n frontend

# Check HTTPRoutes
kubectl get httproute -A

# Check services
kubectl get svc -n backend
kubectl get svc -n frontend
```

All pods should be in `Running` state.

---

## Stage 6: Test Your Application

### Test via IP (Before DNS Propagation)

```bash
# Get Gateway IP
GATEWAY_IP=$(kubectl get gateway external-gateway -n gateway-system \
  -o jsonpath='{.status.addresses[0].value}')

# Test backend
curl -H "Host: api.yourdomain.com" http://$GATEWAY_IP/api/health

# Test frontend
curl -H "Host: www.yourdomain.com" http://$GATEWAY_IP/
```

### Test via Domain (After DNS Propagation)

```bash
# Test backend
curl https://api.yourdomain.com/api/health

# Test frontend
curl https://www.yourdomain.com/
```

---

## Troubleshooting

### Gateway Not Getting IP

```bash
kubectl describe gateway external-gateway -n gateway-system
```

Look for events and conditions.

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

### HTTPRoute Not Working

```bash
kubectl describe httproute -n <namespace>
```

Check if Gateway is attached.

---

## Next Steps

Once dev is working:
1. Repeat for **prod** environment
2. Use production tfvars
3. Deploy to prod via tags (e.g., `backend-v1.0.0`)

---

## Quick Reference

**Terraform Deploy:**
```
Actions → Terraform → Run workflow → Select env & action
```

**K8s Infrastructure:**
```
Actions → Kubernetes Infrastructure → Run workflow → Select env
```

**Application Deploy (Dev):**
```
Push to main → Auto-deploys
```

**Application Deploy (Prod):**
```
git tag backend-v1.0.0
git push origin backend-v1.0.0
```
