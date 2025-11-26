# External Secrets Operator Setup

This directory contains the configuration for External Secrets Operator (ESO) to synchronize secrets from Google Secret Manager to Kubernetes.

## Overview

External Secrets Operator enables automatic synchronization of secrets from Google Secret Manager to Kubernetes Secrets, eliminating the need to store secrets in Git or manually manage them.

## Architecture

```
Google Secret Manager → External Secrets Operator → Kubernetes Secrets → Pods
```

## Prerequisites

1. **GKE Cluster**: Deployed with Workload Identity enabled
2. **Secret Manager**: Secrets created in Google Secret Manager (via Terraform)
3. **IAM Permissions**: Service accounts with `secretmanager.secretAccessor` role
4. **Helm**: Installed on your local machine

## Installation

### 1. Add Helm Repository

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
```

### 2. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 3. Install External Secrets Operator

```bash
# Update PROJECT_ID in helm-values.yaml first
helm upgrade --install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets \
  -f helm-values.yaml \
  --wait
```

### 4. Verify Installation

```bash
kubectl get pods -n external-secrets
kubectl get crds | grep external-secrets
```

Expected CRDs:
- `externalsecrets.external-secrets.io`
- `secretstores.external-secrets.io`
- `clustersecretstores.external-secrets.io`

## Configuration

### SecretStore Setup

Create SecretStore resources for each namespace:

```bash
# Update YOUR_PROJECT_ID in secret-store.yaml
kubectl apply -f secret-store.yaml
```

Verify:
```bash
kubectl get secretstore -n backend
kubectl get secretstore -n database
kubectl get secretstore -n frontend
```

### Create ExternalSecrets

Deploy ExternalSecret resources to sync secrets:

```bash
kubectl apply -f external-secrets.yaml
```

Verify synchronization:
```bash
# Check ExternalSecret status
kubectl get externalsecret -n backend
kubectl describe externalsecret database-credentials -n backend

# Check created Kubernetes Secrets
kubectl get secrets -n backend
kubectl get secret database-credentials -n backend -o yaml
```

## Usage in Pods

Once secrets are synchronized, reference them in your pods:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend-app
  namespace: backend
spec:
  containers:
  - name: app
    image: gcr.io/PROJECT_ID/backend:latest
    env:
    # From ExternalSecret -> Kubernetes Secret
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: database-credentials
          key: password
    - name: DB_URL
      valueFrom:
        secretKeyRef:
          name: database-credentials
          key: url
    - name: JWT_SECRET
      valueFrom:
        secretKeyRef:
          name: jwt-secret
          key: secret
```

## Workload Identity Configuration

Each namespace requires a Kubernetes ServiceAccount with Workload Identity annotation:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dev-backend-sa
  namespace: backend
  annotations:
    iam.gke.io/gcp-service-account: dev-backend-app@PROJECT_ID.iam.gserviceaccount.com
```

The GCP service account must have:
1. `roles/secretmanager.secretAccessor` on specific secrets
2. `roles/iam.workloadIdentityUser` binding to Kubernetes SA

This is already configured in Terraform (`iam.tf`).

## Secret Rotation

ExternalSecrets automatically refresh based on `refreshInterval`:

```yaml
spec:
  refreshInterval: 1h  # Check for updates every hour
```

To force immediate sync:
```bash
kubectl annotate externalsecret database-credentials -n backend \
  force-sync=$(date +%s)
```

## Troubleshooting

### ExternalSecret Not Syncing

```bash
# Check ExternalSecret status
kubectl describe externalsecret <name> -n <namespace>

# Check operator logs
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets
```

Common issues:
- ❌ Secret not found in Secret Manager → Check secret ID
- ❌ Permission denied → Verify Workload Identity and IAM bindings
- ❌ SecretStore not ready → Check SecretStore status

### Workload Identity Issues

```bash
# Verify pod can authenticate
kubectl run -it --rm debug --image=google/cloud-sdk --restart=Never -n backend \
  --overrides='{"spec":{"serviceAccountName":"dev-backend-sa"}}' \
  -- gcloud auth list
```

Should show the GCP service account email.

## Security Best Practices

✅ **Namespace Isolation**: Separate SecretStores per namespace  
✅ **Least Privilege**: Grant minimal IAM permissions per service  
✅ **No Git Commits**: Never commit secret values  
✅ **Automatic Rotation**: Use Secret Manager rotation policies  
✅ **Audit Logging**: Enable Cloud Audit Logs for Secret Manager

## Cost Impact

- **External Secrets Operator**: Free (open source)
- **Secret Manager**: ~$0.06 per 10,000 access operations
- **Estimated**: <$5/month for typical workloads

## Files

- `namespace.yaml` - External Secrets namespace
- `helm-values.yaml` - Helm chart configuration
- `secret-store.yaml` - SecretStore resources per namespace
- `external-secrets.yaml` - Example ExternalSecret resources
- `README.md` - This file

## Next Steps

1. ✅ Install External Secrets Operator
2. ✅ Create SecretStore resources
3. ✅ Deploy ExternalSecret resources
4. Configure application Helm charts to use synced secrets
5. Set up secret rotation policies in Terraform
6. Enable audit logging for Secret Manager access

## References

- [External Secrets Operator Documentation](https://external-secrets.io/)
- [Google Secret Manager Provider](https://external-secrets.io/latest/provider/google-secrets-manager/)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
