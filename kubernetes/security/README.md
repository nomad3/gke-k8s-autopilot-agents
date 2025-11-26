# Security Configuration for GKE Autopilot Cluster

This directory contains security configurations for the GKE Autopilot cluster, implementing defense-in-depth strategies.

## Overview

Security is implemented at multiple layers:

1. **Workload Identity**: Secure pod authentication to GCP services
2. **Pod Security Standards**: Enforce security best practices
3. **Network Policies**: Control pod-to-pod communication
4. **Secret Management**: Google Secret Manager integration
5. **RBAC**: Role-based access control (coming in Phase 3)

## Files

- `service-accounts.yaml` - Kubernetes ServiceAccounts with Workload Identity
- `pod-security-standards.yaml` - Namespace security enforcement
- `network-policies.yaml` - Pod network isolation (in `../network-policies/`)

## Workload Identity Setup

Workload Identity enables pods to authenticate as GCP service accounts without JSON keys.

### Prerequisites

1. GKE cluster with Workload Identity enabled ✅ (done in Terraform)
2. GCP service accounts created ✅ (done in Terraform)
3. IAM bindings configured ✅ (done in Terraform)

### Deploy Service Accounts

```bash
# Update PROJECT_ID in service-accounts.yaml first
kubectl apply -f service-accounts.yaml
```

### Usage in Deployments

Reference the ServiceAccount in your pod specs:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-app
  namespace: backend
spec:
  template:
    spec:
      serviceAccountName: dev-backend-sa  # ← Use Workload Identity SA
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/backend:latest
        # No credentials needed, automatic GCP authentication!
```

### Verify Workload Identity

```bash
# Deploy a test pod
kubectl run -it --rm gcloud-test \
  --image=google/cloud-sdk:slim \
  --restart=Never \
  --namespace=backend \
  --serviceaccount=dev-backend-sa \
  -- gcloud auth list

# Should show: dev-backend-app@PROJECT_ID.iam.gserviceaccount.com
```

## Pod Security Standards

Pod Security Standards are enforced at the namespace level using labels.

### Security Levels

- **restricted**: Most secure, recommended for applications
- **baseline**: Minimally restrictive, prevents known privilege escalations
- **privileged**: Unrestricted (not recommended)

### Applied Levels

| Namespace | Level | Rationale |
|-----------|-------|-----------|
| `backend` | restricted | Application workload |
| `frontend` | restricted | Application workload |
| `database` | baseline | May need some filesystem access |
| `monitoring` | baseline | Tools may need elevated permissions |

### Create Namespaces with Security

```bash
kubectl apply -f pod-security-standards.yaml
```

### Restricted Pod Requirements

To comply with **restricted** level:

✅ **Must have**:
- `securityContext.runAsNonRoot: true`
- `securityContext.allowPrivilegeEscalation: false`
- `securityContext.capabilities.drop: [ALL]`
- `securityContext.seccompProfile.type: RuntimeDefault`

✅ **Must NOT**:
- Run as root (UID 0)
- Use privileged containers
- Use host namespaces
- Mount hostPath volumes

### Example Compliant Pod

See `pod-security-standards.yaml` for a complete example.

## Network Policies

Network Policies control traffic between pods and namespaces.

### Strategy

1. **Default Deny**: Block all traffic by default
2. **Explicit Allow**: Only allow necessary traffic

### Apply Network Policies

```bash
kubectl apply -f ../network-policies/network-policies.yaml
```

### Traffic Flow

```
Internet → Ingress → Frontend → Backend → Database
                         ↓
                    External APIs
```

### Policy Summary

| From | To | Port | Purpose |
|------|----|----- |---------|
| Ingress | Frontend | 3000 | Web traffic |
| Frontend | Backend | 8080 | API calls |
| Backend | Database | 5432 | Data access |
| All | kube-dns | 53 | DNS resolution |
| Backend/Database | Internet | 443 | External APIs |

### Verify Network Policies

```bash
# Check policies
kubectl get networkpolicy -A

# Test connectivity (should fail if blocked)
kubectl run -it --rm test-pod --image=busybox -n frontend -- wget -O- backend.backend:8080
```

## Security Checklist

### Workload Identity
- [x] GKE cluster has Workload Identity enabled
- [x] GCP service accounts created
- [x] IAM bindings configured
- [ ] Kubernetes ServiceAccounts deployed
- [ ] Pods configured to use ServiceAccounts

### Pod Security
- [ ] Namespaces created with security labels
- [ ] Deployments use non-root users
- [ ] Read-only root filesystem where possible
- [ ] Capabilities dropped
- [ ] Seccomp profile applied

### Network Security
- [ ] Network policies deployed
- [ ] Default deny policies applied
- [ ] Explicit allow rules configured
- [ ] DNS access enabled
- [ ] External access limited

### Secret Management
- [x] Google Secret Manager configured
- [ ] External Secrets Operator deployed
- [ ] SecretStore created per namespace
- [ ] ExternalSecrets configured
- [ ] Applications using synced secrets

## Cost Impact

- **Workload Identity**: Free
- **Pod Security Standards**: Free (built-in)
- **Network Policies**: Free (built-in with Dataplane V2)
- **Secret Manager**: ~$0.06 per 10,000 operations

**Total**: <$5/month for security features

## Troubleshooting

### Workload Identity Not Working

**Symptoms**: Permission denied errors from GCP APIs

**Debug**:
```bash
# Check ServiceAccount annotation
kubectl get sa dev-backend-sa -n backend -o yaml

# Verify IAM binding
gcloud iam service-accounts get-iam-policy \
  dev-backend-app@PROJECT_ID.iam.gserviceaccount.com

# Test from pod
kubectl run -it test --image=google/cloud-sdk \
  --serviceaccount=dev-backend-sa -n backend \
  -- gcloud auth list
```

### Pod Rejected by Security Policy

**Symptoms**: Error: `pods "X" is forbidden: violates PodSecurity`

**Fix**: Update pod spec to meet restricted requirements:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
```

### Network Policy Blocking Traffic

**Symptoms**: Pods can't communicate

**Debug**:
```bash
# Check if policies exist
kubectl get netpol -n backend

# Temporarily remove policy to test
kubectl delete netpol backend-allow-ingress -n backend

# Check pod labels match policy selectors
kubectl get pods -n backend --show-labels
```

## Best Practices

✅ **Always use Workload Identity** (never JSON keys)  
✅ **Apply Pod Security Standards** at namespace level  
✅ **Start with default-deny** network policies  
✅ **Use non-root users** in containers  
✅ **Drop all capabilities** unless specific ones needed  
✅ **Enable read-only root filesystem** where possible  
✅ **Never commit secrets** to Git  
✅ **Rotate secrets regularly** using Secret Manager  
✅ **Audit security configurations** periodically

## Next Steps

1. Deploy ServiceAccounts: `kubectl apply -f service-accounts.yaml`
2. Create secure namespaces: `kubectl apply -f pod-security-standards.yaml`
3. Apply network policies: `kubectl apply -f ../network-policies/network-policies.yaml`
4. Update Helm charts to use secure pod specs
5. Configure applications to use Workload Identity
6. Test end-to-end security

## References

- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [GKE Security Best Practices](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster)
