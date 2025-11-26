# Namespaces and RBAC Configuration

This directory contains namespace definitions and Role-Based Access Control (RBAC) policies for the GKE cluster.

## Overview

Namespaces provide logical isolation for workloads, while RBAC controls who can do what in each namespace.

## Files

- `namespaces.yaml` - Namespace definitions with Pod Security labels
- `rbac.yaml` - Roles, RoleBindings, and Resource Quotas

## Namespaces

| Namespace | Purpose | Security Level | Resource Quota |
|-----------|---------|----------------|----------------|
| `frontend` | Web application frontend | Restricted | 2 CPU, 4Gi RAM |
| `backend` | API and backend services | Restricted | 4 CPU, 8Gi RAM |
| `database` | Database workloads | Baseline | 4 CPU, 8Gi RAM |
| `monitoring` | Observability tools | Baseline | 2 CPU, 4Gi RAM |
| `ingress-nginx` | Ingress controller | Baseline | N/A |
| `external-secrets` | Secret synchronization | Baseline | N/A |

## Setup

### Create Namespaces

```bash
kubectl apply -f namespaces.yaml
```

### Verify Namespaces

```bash
kubectl get namespaces
kubectl get ns -L pod-security.kubernetes.io/enforce
```

## RBAC Configuration

### Roles Defined

**Per Namespace**:
- `backend-developer` - Full access to backend resources
- `backend-viewer` - Read-only access to backend
- `frontend-developer` - Full access to frontend resources
- `database-operator` - Database management including exec access

**Cluster-wide**:
- `monitoring-metrics-reader` - Read metrics from all namespaces
- `cicd-deployer` - Deploy applications across namespaces

### Apply RBAC

```bash
# Update PROJECT_ID in rbac.yaml first
kubectl apply -f rbac.yaml
```

### Verify RBAC

```bash
#Check roles
kubectl get roles -A

# Check rolebindings
kubectl get rolebindings -A

# Check clusterroles
kubectl get clusterroles | grep -E "monitoring|cicd"

# Check resource quotas
kubectl get resourcequota -A
```

## Resource Quotas

Resource quotas prevent runaway resource consumption and control costs:

### Backend Namespace
- CPU Requests: 4 cores
- Memory Requests: 8Gi
- PVCs: 5
- LoadBalancers: 0 (prevented)

### Frontend Namespace
- CPU Requests: 2 cores
- Memory Requests: 4Gi
- PVCs: 2
- LoadBalancers: 0

### Database Namespace
- CPU Requests: 4 cores
- Memory Requests: 8Gi
- PVCs: 10 (for data storage)
- LoadBalancers: 0

### Check Quota Usage

```bash
# View quota and usage
kubectl describe resourcequota -n backend
kubectl describe resourcequota -n frontend
kubectl describe resourcequota -n database
```

## Service Accounts

Each namespace has dedicated service accounts with Workload Identity:

| Namespace | ServiceAccount | GCP Service Account |
|-----------|----------------|---------------------|
| backend | dev-backend-sa | dev-backend-app@PROJECT_ID |
| frontend | dev-frontend-sa | dev-frontend-app@PROJECT_ID |
| database | dev-database-sa | dev-database-app@PROJECT_ID |
| monitoring | monitoring-sa | gke-autopilot-cluster-monitoring@PROJECT_ID |
| kube-system | cicd-deployer-sa | gke-autopilot-cluster-cicd@PROJECT_ID |

## Testing RBAC

### Test ServiceAccount Permissions

```bash
# Can the backend SA create deployments?
kubectl auth can-i create deployments --as=system:serviceaccount:backend:dev-backend-sa -n backend
# Should return: yes

# Can the backend SA create deployments in frontend?
kubectl auth can-i create deployments --as=system:serviceaccount:backend:dev-backend-sa -n frontend
# Should return: no

# Can viewer read secrets?
kubectl auth can-i get secrets --as=system:serviceaccount:backend:backend-viewer -n backend
# Should return: no
```

### Test with Real Pod

```bash
# Run a pod with ServiceAccount
kubectl run test-pod --image=bitnami/kubectl \
  --serviceaccount=dev-backend-sa \
  -n backend \
  --command -- sleep infinity

# Exec into pod and test permissions
kubectl exec -it test-pod -n backend -- kubectl get pods -n backend
# Should work

kubectl exec -it test-pod -n backend -- kubectl get pods -n frontend
# Should fail (forbidden)

# Cleanup
kubectl delete pod test-pod -n backend
```

## CI/CD ServiceAccount

The `cicd-deployer-sa` in `kube-system` has cluster-wide deployment permissions:

```bash
# Create service account token for CI/CD (Kubernetes 1.24+)
kubectl create token cicd-deployer-sa -n kube-system --duration=8760h

# Or create a long-lived secret (deprecated but still works)
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: cicd-deployer-token
  namespace: kube-system
  annotations:
    kubernetes.io/service-account.name: cicd-deployer-sa
type: kubernetes.io/service-account-token
EOF

# Get token
kubectl get secret cicd-deployer-token -n kube-system -o jsonpath='{.data.token}' | base64 -d
```

## Pod Security Standards

Enforced via namespace labels:

### Restricted Level
Applied to: `frontend`, `backend`

**Requirements**:
- ✅ Run as non-root
- ✅ No privilege escalation
- ✅ Drop all capabilities
- ✅ Seccomp profile
- ✅ Read-only root filesystem (recommended)

### Baseline Level
Applied to: `database`, `monitoring`, `ingress-nginx`

**Requirements**:
- ✅ No privileged containers
- ✅ No host namespaces
- ✅ Limited capabilities
- ⚠️ May run as root if needed

## Modifying RBAC

### Add New Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-custom-role
  namespace: backend
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update"]
```

### Create RoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-custom-binding
  namespace: backend
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: my-custom-role
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: backend
```

## Troubleshooting

### Permission Denied Errors

```bash
# Check what permissions a SA has
kubectl auth can-i --list --as=system:serviceaccount:backend:dev-backend-sa -n backend

# Describe role to see rules
kubectl describe role backend-developer -n backend

# Check rolebinding
kubectl describe rolebinding backend-sa-developer-binding -n backend
```

### Resource Quota Exceeded

```bash
# View quota usage
kubectl describe resourcequota backend-quota -n backend

# Check actual usage
kubectl top pods -n backend

# Solution: Reduce resource requests or increase quota
```

### Pod Security Policy Violation

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Update pod security context to meet requirements
# See: kubernetes/security/pod-security-standards.yaml
```

## Best Practices

✅ **Least Privilege**: Grant minimal necessary permissions  
✅ **Namespace Isolation**: Use namespaces for logical separation  
✅ **Resource Quotas**: Prevent resource exhaustion  
✅ **ServiceAccounts**: Never use default SA for applications  
✅ **Workload Identity**: Use for GCP authentication  
✅ **Pod Security**: Enforce restricted level where possible  
✅ **Regular Audits**: Review RBAC policies periodically

## Next Steps

1. ✅ Create namespaces with security labels
2. ✅ Apply RBAC roles and bindings
3. Update PROJECT_ID in service account annotations
4. Deploy applications using namespaced ServiceAccounts
5. Monitor resource quota usage
6. Set up namespace-specific monitoring

## References

- [Kubernetes Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
