# CI/CD Pipeline - GitHub Actions

Automated CI/CD pipelines for deploying to GKE Autopilot clusters using GitHub Actions.

## Workflows

### 1. Development Deployment (`deploy-dev.yaml`)
**Trigger**: Push to `main` or `develop` branches

**Stages**:
1. **Code Quality** - Linting, unit tests, type checking
2. **Build** - Docker images for backend and frontend
3. **Scan** - Trivy vulnerability scanning (non-blocking)
4. **Push** - Push to GCR with git SHA tags
5. **Deploy** - Automated deployment to dev GKE cluster

**Image Tags**: `{sha}`, `dev-latest`

### 2. Production Deployment (`deploy-prod.yaml`)
**Trigger**: Push tags matching `v*.*.*` (e.g., `v1.0.0`)

**Stages**:
1. **Quality Gates** - Comprehensive testing and build checks
2. **Build** - Docker images with version tags
3. **Scan** - Trivy scanning (BLOCKS on critical vulnerabilities)
4. **Push** - Push to production GCR
5. **Deploy** - Deploy to production (requires approval)
6. **Smoke Tests** - Post-deployment validation
7. **Release** - Create GitHub release

**Image Tags**: `{version}`, `latest`

**Features**:
- Requires GitHub environment approval
- Atomic deployments (auto-rollback on failure)
- Backup of current deployment
- Smoke test validation

### 3. Pull Request Checks (`pr-checks.yaml`)
**Trigger**: Pull requests to `main` or `develop`

**Checks**:
- Linting
- Unit tests with coverage
- Build validation
- Docker build test
- Helm template validation

## Setup Requirements

### GitHub Secrets

Configure these secrets in your GitHub repository:

**Dev Environment**:
- `GCP_PROJECT_ID_DEV` - GCP project ID for dev
- `GCP_SA_KEY_DEV` - Service account JSON key for dev

**Production Environment**:
- `GCP_PROJECT_ID_PROD` - GCP project ID for production
- `GCP_SA_KEY_PROD` - Service account JSON key for production

### Creating Service Account Keys

```bash
# Dev environment
gcloud iam service-accounts create github-actions-dev \
  --display-name="GitHub Actions Dev" \
  --project=PROJECT_ID_DEV

gcloud projects add-iam-policy-binding PROJECT_ID_DEV \
  --member="serviceAccount:github-actions-dev@PROJECT_ID_DEV.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding PROJECT_ID_DEV \
  --member="serviceAccount:github-actions-dev@PROJECT_ID_DEV.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud iam service-accounts keys create github-sa-dev-key.json \
  --iam-account=github-actions-dev@PROJECT_ID_DEV.iam.gserviceaccount.com

# Repeat for production with prod project ID
```

### GitHub Environment Protection (Production)

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Add protection rules:
   - ✅ Required reviewers (at least 1)
   - ✅ Wait timer: 5 minutes (optional)
   - ✅ Branch restrictions: `main` only

## Usage

### Deploy to Dev

```bash
# Commit and push to main
git add .
git commit -m "feat: add new feature"
git push origin main

# Automatic deployment to dev will start
```

### Deploy to Production

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# Workflow will:
# 1. Run all quality checks
# 2. Build and scan images
# 3. Wait for approval (if configured)
# 4. Deploy to production
# 5. Create GitHub release
```

## Workflow Features

### Security Scanning (Trivy)

**Dev**: Non-blocking, reports uploaded to GitHub Security
**Prod**: Blocks deployment on CRITICAL/HIGH vulnerabilities

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail in prod
```

### Docker Image Caching

Uses GitHub Actions cache for faster builds:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### Atomic Deployments

Production deployments use `--atomic` flag:

```bash
helm upgrade --install backend \
  --atomic  # Rollback if deployment fails
  --timeout 10m
```

### Deployment Verification

Automated verification after deployment:

```yaml
- name: Verify deployment
  run: |
    kubectl rollout status deployment/backend -n backend --timeout=10m
```

## Image Tagging Strategy

| Environment | Tag Format | Example |
|-------------|------------|---------|
| Dev | `{git-sha}`, `dev-latest` | `abc1234`, `dev-latest` |
| Prod | `{version}`, `latest` | `v1.0.0`, `latest` |

## Pipeline Flow

### Dev Pipeline
```
Push to main
  ↓
Quality Checks (lint, test)
  ↓
Build Images (backend, frontend)
  ↓
Scan with Trivy
  ↓
Push to GCR
  ↓
Deploy to Dev GKE
  ↓
Verify Deployment
```

### Production Pipeline
```
Push tag v1.0.0
  ↓
Quality Gates (lint, test, build)
  ↓
Build Production Images
  ↓
Scan with Trivy (BLOCKS on HIGH/CRITICAL)
  ↓
Push to Production GCR
  ↓
Wait for Approval ⏸
  ↓
Backup Current Deployment
  ↓
Deploy to Prod GKE (Atomic)
  ↓
Run Smoke Tests
  ↓
Create GitHub Release
```

## Monitoring Deployments

### GitHub Actions UI

View workflow runs at: `https://github.com/YOUR_ORG/YOUR_REPO/actions`

### Check Deployment Status

```bash
# Get cluster credentials
gcloud container clusters get-credentials gke-autopilot-cluster-dev \
  --region us-central1

# Check deployment status
kubectl get deployments -A
kubectl rollout status deployment/backend -n backend

# View recent deployments
helm history backend -n backend
```

## Rollback Procedures

### Automatic Rollback

Production deployments automatically rollback on failure (--atomic flag).

### Manual Rollback

```bash
# Get cluster credentials
gcloud container clusters get-credentials gke-autopilot-cluster-prod \
  --region us-central1 \
  --project PROJECT_ID_PROD

# Rollback to previous release
helm rollback backend -n backend

# Or rollback to specific revision
helm history backend -n backend
helm rollback backend 3 -n backend
```

## Customization

### Add Environment-Specific Steps

```yaml
- name: Run migrations
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: |
    kubectl exec -n backend deployment/backend -- npm run migrate
```

### Add Slack Notifications

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Deployment ${{ job.status }}: ${{ github.repository }}"
      }
```

### Add Performance Testing

```yaml
- name: Run load tests
  run: |
    kubectl run k6 --image=grafana/k6 \
      --restart=Never \
      -- run /scripts/load-test.js
```

## Troubleshooting

### Deployment Fails

**Check workflow logs**:
- Go to Actions tab
- Click on failed workflow
- Review each step's logs

**Common issues**:
- Missing secrets: Add required GitHub secrets
- GKE permissions: Verify service account roles
- Helm timeout: Increase `--timeout` value
- Image not found: Check GCR push succeeded

### Trivy Blocking Deployment

```bash
# View vulnerability report in GitHub Security tab
# Options:
# 1. Fix vulnerabilities (update dependencies)
# 2. Add exception (not recommended for production)
# 3. Lower severity threshold temporarily
```

### Helm Deployment Timeout

```yaml
# Increase timeout in workflow
--timeout 15m  # Default is 10m
```

## Best Practices

✅ **Always test in dev** before promoting to prod  
✅ **Use semantic versioning** for production tags  
✅ **Review Security scan results** before deploying  
✅ **Set up environment protection** for production  
✅ **Monitor deployments** after release  
✅ **Have rollback plan** ready  
✅ **Use atomic deployments** in production  
✅ **Add smoke tests** after deployment  
✅ **Keep secrets secure** (never commit to repo)  
✅ **Document deployment process** for team

## Cost Impact

GitHub Actions costs:
- **Public repositories**: Free unlimited minutes
- **Private repositories**: 2,000 minutes/month free (then ~$0.008/minute)

Typical workflow execution:
- Dev deployment: ~5-10 minutes
- Prod deployment: ~10-15 minutes

## Next Steps

1. Add GitHub secrets for GCP service accounts
2. Configure GitHub environment protection for production
3. Customize workflows for your application structure
4. Add notification integrations (Slack, email)
5. Set up monitoring and alerting for deployments
6. Create runbooks for common deployment issues
