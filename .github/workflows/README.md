# GitHub Actions Workflows

This directory contains CI/CD pipelines for automated testing, building, and deployment.

## Workflow Organization

### Application Workflows
- `backend-dev.yaml` - Backend deployment to dev environment (auto on push to main)
- `backend-prod.yaml` - Backend deployment to prod environment (on tag or manual)
- `frontend-dev.yaml` - Frontend deployment to dev environment (auto on push to main)
- `frontend-prod.yaml` - Frontend deployment to prod environment (on tag or manual)

### Infrastructure Workflows
- `terraform-deploy.yaml` - **Unified Terraform workflow** for both dev and prod
- `terraform-pr.yaml` - Terraform validation on pull requests

### Quality Workflows
- `pr-checks.yaml` - Code quality, tests, and build validation on PRs

---

## Terraform Workflow (New Approach)

### Why Consolidated?

The Terraform workflow uses a **single file with environment selection** because:
- ✅ Infrastructure changes should always be deliberate (no auto-apply)
- ✅ Same deployment process for all environments
- ✅ Reduces duplication and maintenance
- ✅ Environment selected via dropdown (safer)

### Usage

#### Plan Changes
1. Go to **Actions** → **Terraform Deploy**
2. Click **Run workflow**
3. Select environment: `dev` or `prod`
4. Select action: `plan`
5. Review the plan output

#### Apply Changes
1. Go to **Actions** → **Terraform Deploy**
2. Click **Run workflow**
3. Select environment: `dev` or `prod`
4. Select action: `apply`
5. **Production requires manual approval** (if configured in GitHub environments)

### Required GitHub Secrets

#### Development
- `GCP_SA_KEY_DEV` - GCP service account key for dev
- `GCS_BUCKET_DEV` - Terraform state bucket (e.g., `myproject-dev-terraform-state`)

#### Production
- `GCP_SA_KEY_PROD` - GCP service account key for prod
- `GCS_BUCKET_PROD` - Terraform state bucket (e.g., `myproject-prod-terraform-state`)

---

## Application Workflows (Separate Files)

### Why Separate for Applications?

Application workflows remain **separate per environment** because:
- Different triggers (auto-deploy dev, manual/tag for prod)
- Different security requirements (Trivy blocking in prod)
- Different approval gates
- Clearer workflow run history

### Triggers

#### Development
```yaml
on:
  push:
    branches: [main, develop]
    paths: ['backend/**']
```

#### Production
```yaml
on:
  push:
    tags: ['backend-v*']  # e.g., backend-v1.2.3
```

### Deployment Flow

**Dev:**
1. Push to `main` branch
2. Workflow auto-triggers
3. Runs tests
4. Builds Docker image
5. Deploys to dev cluster

**Prod:**
1. Create tag: `git tag backend-v1.2.3`
2. Push tag: `git push origin backend-v1.2.3`
3. Workflow triggers
4. Runs security scan (Trivy)
5. **Blocks if vulnerabilities found**
6. Requires manual approval (if configured)
7. Deploys to prod cluster

---

## GitHub Environments Configuration

### Setup Environments (Recommended)

1. Go to **Settings** → **Environments**
2. Create `development` environment
3. Create `production` environment
4. For production, enable:
   - **Required reviewers** (select team members)
   - **Wait timer** (optional delay)
   - **Deployment branches** (only tags or main)

This adds a manual approval step before production deployments.

---

## Workflow Secrets Setup

See [GitHub Secrets Setup Guide](../docs/github-secrets-setup.md) for detailed instructions.

### Quick Reference

All workflows need these secrets:

| Secret Name | Used In | Description |
|-------------|---------|-------------|
| `GCP_PROJECT_ID_DEV` | App Dev, Terraform Deploy | Dev GCP project ID |
| `GCP_PROJECT_ID_PROD` | App Prod, Terraform Deploy | Prod GCP project ID |
| `GCP_SA_KEY_DEV` | App Dev, Terraform Deploy | Dev service account JSON |
| `GCP_SA_KEY_PROD` | App Prod, Terraform Deploy | Prod service account JSON |
| `GCS_BUCKET_DEV` | Terraform Deploy | Dev state bucket name |
| `GCS_BUCKET_PROD` | Terraform Deploy | Prod state bucket name |

---

## Best Practices

### For Infrastructure (Terraform)
- ✅ **Always run plan first** before apply
- ✅ **Review plan output** carefully
- ✅ **Use manual trigger** (no auto-apply)
- ✅ **Separate state per environment** (different buckets or prefixes)

### For Applications
- ✅ **Test in dev first** before prod deployment
- ✅ **Use semantic versioning** for prod tags (v1.2.3)
- ✅ **Monitor deployments** in GCP Console
- ✅ **Enable rollback** (Helm atomic flag)

### Security
- ✅ **Scan images** before production deployment
- ✅ **Rotate service account keys** every 90 days
- ✅ **Limit workflow permissions** using OIDC (future enhancement)
- ✅ **Review workflow logs** for sensitive data leaks

---

## Troubleshooting

### Terraform State Lock

**Error:** `Error acquiring the state lock`

**Solution:**
```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

### Failed Deployment

**Check:**
1. Workflow logs in GitHub Actions
2. GKE cluster events: `kubectl get events -n NAMESPACE`
3. Pod logs: `kubectl logs -n NAMESPACE POD_NAME`

### Permission Denied

**Check:**
1. Service account has required roles
2. Workload Identity bindings are correct
3. GitHub secrets are up to date

---

## Migration from Old Workflows

### What Changed?

**Old:**
- `terraform-dev.yaml` - Auto-applied on push
- `terraform-prod.yaml` - Applied on tag

**New:**
- `terraform-deploy.yaml` - Manual trigger with environment dropdown
- `terraform-pr.yaml` - PR validation

### Benefits

- ✅ No accidental infrastructure changes
- ✅ Clear approval process
- ✅ Single source of truth
- ✅ Easier maintenance

---

## Future Enhancements

- [ ] Add OIDC authentication (remove service account keys)
- [ ] Implement Terraform Cloud/Atlantis for plan comments
- [ ] Add cost estimation in PR comments
- [ ] Enable drift detection on schedule
