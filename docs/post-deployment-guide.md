# Post-Cluster Deployment Guide: Best Practices

This guide covers the essential steps and best practices for deploying applications to your GKE Autopilot cluster after the infrastructure is provisioned.

---

## 1. Helm Chart Deployment Strategy

### Preparation
- **Connect to Cluster**: 
  ```bash
  gcloud container clusters get-credentials CLUSTER_NAME --region REGION --project PROJECT_ID
  ```
- **Verify Workload Identity**: Ensure Kubernetes Service Accounts are bound to GCP Service Accounts (already configured in Terraform)

### Deployment Order
1. **Database First**: Deploy databases with persistent storage
2. **Backend Services**: Deploy API/backend services that depend on databases
3. **Frontend**: Deploy frontend applications last

### Best Practices
- **Use Helm Values Files**: Separate `values-dev.yaml` and `values-prod.yaml` for environment-specific configs
- **Version Control**: Pin Helm chart versions in production
- **Resource Limits**: Always set CPU/memory requests and limits (Autopilot requires this)
- **Health Checks**: Configure `livenessProbe` and `readinessProbe` for all services
- **Rolling Updates**: Use `RollingUpdate` strategy with `maxSurge` and `maxUnavailable`

### Example Deployment
```bash
# Deploy backend
helm upgrade --install backend ./helm/charts/microservice \
  -f ./helm/values/backend-prod.yaml \
  --namespace backend \
  --create-namespace

# Deploy frontend
helm upgrade --install frontend ./helm/charts/microservice \
  -f ./helm/values/frontend-prod.yaml \
  --namespace frontend \
  --create-namespace
```

---

## 2. GitHub Actions CI/CD Workflows

### Workflow Structure
Your workflows should follow this pattern:

#### PR Checks (on pull_request)
1. **Lint**: Code quality checks
2. **Unit Tests**: Run test suites
3. **Security Scan**: Trivy/Snyk for vulnerabilities
4. **Build**: Docker build (no push)

#### Dev Deployment (on push to main)
1. **Build**: Create Docker image
2. **Tag**: Use commit SHA or semantic version
3. **Push**: Push to Artifact Registry
4. **Deploy**: Update Helm release in dev cluster
5. **Verify**: Run smoke tests

#### Prod Deployment (on tag or manual)
1. **Build**: Create production image
2. **Scan**: Security scan with strict policies
3. **Push**: Push to production registry
4. **Approval**: Manual approval gate
5. **Deploy**: Blue/green or canary deployment
6. **Verify**: Health checks and integration tests

### Best Practices
- **Separate Workflows**: One per service (backend-dev.yaml, backend-prod.yaml)
- **Path Filters**: Only trigger on relevant file changes
- **Caching**: Cache Docker layers and dependencies
- **Artifacts**: Store test results and build logs
- **Notifications**: Slack/email on failures
- **Rollback**: Automated rollback on health check failures

### Required GitHub Secrets
- `GCP_SA_KEY_DEV` / `GCP_SA_KEY_PROD`: Service account keys
- `GCP_PROJECT_ID_DEV` / `GCP_PROJECT_ID_PROD`: Project IDs
- `GKE_CLUSTER_NAME_DEV` / `GKE_CLUSTER_NAME_PROD`: Cluster names
- `GKE_REGION`: Cluster region

---

## 3. Secrets Management with GCP Secret Manager

### Architecture
```
GCP Secret Manager → Workload Identity → Kubernetes Service Account → Pod
```

### Setup Process

#### Step 1: Create Secrets in Secret Manager
```bash
# Create secret
echo -n "my-secret-value" | gcloud secrets create db-password \
  --data-file=- \
  --project=PROJECT_ID

# Add version
echo -n "new-value" | gcloud secrets versions add db-password \
  --data-file=-
```

#### Step 2: Grant Access via Workload Identity
Already configured in your Terraform (`iam.tf`):
- GCP Service Account: `dev-backend-app@PROJECT.iam.gserviceaccount.com`
- K8s Service Account: `dev-backend-sa` in namespace `backend`
- Binding: Allows K8s SA to impersonate GCP SA

#### Step 3: Access Secrets in Pods

**Option A: External Secrets Operator (Recommended)**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: backend-secrets
spec:
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: backend-secrets
  data:
  - secretKey: db-password
    remoteRef:
      key: dev-database-password
```

**Option B: Init Container**
Fetch secrets in an init container and write to shared volume.

**Option C: Application Code**
Use GCP SDK to fetch secrets directly (less recommended).

### Best Practices
- **Rotation**: Enable automatic rotation for sensitive secrets
- **Versioning**: Use versioned secrets for rollback capability
- **Least Privilege**: Grant access only to required secrets
- **Audit Logs**: Enable Secret Manager audit logging
- **Never Hardcode**: No secrets in Helm values or ConfigMaps

---

## 4. Container Registry Setup

### Artifact Registry (Recommended)
Your Terraform already creates Artifact Registry repositories.

#### Configure Docker Authentication
```bash
gcloud auth configure-docker REGION-docker.pkg.dev
```

#### Push Images
```bash
# Tag image
docker tag myapp:latest REGION-docker.pkg.dev/PROJECT/REPO/myapp:v1.0.0

# Push
docker push REGION-docker.pkg.dev/PROJECT/REPO/myapp:v1.0.0
```

#### Pull in GKE
GKE nodes automatically authenticate via Workload Identity (configured in Terraform).

### Image Naming Convention
```
REGION-docker.pkg.dev/PROJECT/REPO/SERVICE:TAG
```

**Tag Strategy:**
- Dev: `dev-{commit-sha}` or `dev-latest`
- Prod: `v1.0.0` (semantic versioning)

### Best Practices
- **Vulnerability Scanning**: Enable automatic scanning in Artifact Registry
- **Binary Authorization**: Enforce signed images (configured in Terraform)
- **Cleanup Policies**: Remove old untagged images (already in Terraform)
- **Multi-Region**: Replicate critical images across regions
- **Immutable Tags**: Use digest references in production

---

## 5. Observability & Monitoring

### Google Cloud Monitoring (Already Enabled)
Your Terraform enables:
- **Cloud Monitoring**: Metrics from cluster and workloads
- **Cloud Logging**: Centralized logs
- **Managed Prometheus**: For custom metrics

### Post-Deployment Setup

#### 1. Install Monitoring Stack
```bash
# Install Prometheus Operator (optional, for custom metrics)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

#### 2. Configure Dashboards
- **Import Terraform Dashboard**: Use `terraform/dashboards/gke-overview.json`
- **Create Custom Dashboards**: For application-specific metrics

#### 3. Set Up Alerts
```yaml
# Example alert for high error rate
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backend-alerts
spec:
  groups:
  - name: backend
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
      annotations:
        summary: "High error rate detected"
```

#### 4. Distributed Tracing
- **Cloud Trace**: Automatically enabled for GKE
- **OpenTelemetry**: Instrument applications for detailed traces

### Logging Best Practices
- **Structured Logging**: Use JSON format
- **Log Levels**: DEBUG in dev, INFO in prod
- **Correlation IDs**: Track requests across services
- **Log Retention**: Configure retention policies (30-90 days)

### Key Metrics to Monitor
- **Cluster**: CPU/memory utilization, pod count, node health
- **Application**: Request rate, error rate, latency (RED metrics)
- **Database**: Connection pool, query latency, deadlocks
- **Network**: Ingress traffic, egress costs

---

## 6. Security Hardening

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Pod Security Standards
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: backend
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

### Additional Security Measures
1. **Enable GKE Security Posture**: Review security recommendations
2. **Vulnerability Scanning**: Scan images in CI/CD
3. **RBAC**: Implement least-privilege access
4. **Audit Logging**: Enable GKE audit logs
5. **Secrets Encryption**: Enable at-rest encryption (default in GKE)
6. **mTLS**: Consider service mesh (Istio/Anthos Service Mesh)

---

## 7. Post-Deployment Checklist

### Immediate (Day 1)
- [ ] Verify cluster connectivity
- [ ] Deploy Helm charts to dev environment
- [ ] Test Workload Identity integration
- [ ] Validate Secret Manager access
- [ ] Configure monitoring dashboards
- [ ] Set up basic alerts

### Week 1
- [ ] Deploy to production with manual approval
- [ ] Configure backup policies
- [ ] Set up log aggregation
- [ ] Implement network policies
- [ ] Run security scans
- [ ] Document runbooks

### Ongoing
- [ ] Monitor costs and optimize resources
- [ ] Review security posture monthly
- [ ] Rotate service account keys (90 days)
- [ ] Update Helm charts and dependencies
- [ ] Conduct disaster recovery drills
- [ ] Review and update alerts

---

## 8. Troubleshooting Common Issues

### Pods Not Starting
- Check Workload Identity bindings
- Verify image pull permissions
- Review resource requests/limits
- Check Secret Manager access

### High Costs
- Review Autopilot resource allocation
- Optimize pod resource requests
- Enable cluster autoscaling
- Use committed use discounts

### Performance Issues
- Check pod CPU/memory throttling
- Review database connection pooling
- Optimize image sizes
- Enable HTTP/2 and gRPC

---

## Next Steps

1. **Review Existing Workflows**: Check `.github/workflows/` for current CI/CD setup
2. **Test in Dev**: Deploy to dev cluster first
3. **Gradual Rollout**: Use canary deployments for production
4. **Monitor Closely**: Watch metrics during initial deployments
5. **Iterate**: Continuously improve based on operational experience

For detailed implementation, refer to:
- `docs/github-secrets-setup.md` - GitHub secrets configuration
- `terraform/` - Infrastructure as Code
- `helm/` - Application deployment manifests
