# Network Policies for GKE Autopilot

This directory contains NetworkPolicy resources to control pod-to-pod communication and implement network segmentation.

## Overview

Network Policies provide layer 3/4 traffic filtering between pods in the cluster. GKE Autopilot uses Dataplane V2 (Cilium-based) for advanced network policy enforcement.

## Strategy

**Defense in Depth**:
1. Default deny all traffic
2. Explicitly allow only necessary traffic
3. Namespace-based isolation

## Files

- `network-policies.yaml` - All network policy configurations

## Prerequisites

- GKE cluster with Dataplane V2 ✅ (enabled in Terraform)
- Namespaces created with proper labels
- Pods with correct labels

## Apply Network Policies

```bash
# Apply all policies
kubectl apply -f network-policies.yaml

# Verify
kubectl get networkpolicy -A
```

## Policy Details

### Backend Namespace

**Ingress (allowed)**:
- ✅ From `frontend` namespace on port 8080
- ✅ From `ingress-nginx` namespace on port 8080

**Egress (allowed)**:
- ✅ To `kube-system` (DNS) on port 53
- ✅ To `database` namespace on port 5432
- ✅ To internet on port 443 (HTTPS)

### Frontend Namespace

**Ingress (allowed)**:
- ✅ From `ingress-nginx` namespace on port 3000
- ✅ From anywhere on port 3000 (public-facing)

**Egress (allowed)**:
- ✅ To `kube-system` (DNS) on port 53
- ✅ To `backend` namespace on port 8080
- ✅ To internet on port 443 (HTTPS for CDNs)

### Database Namespace

**Ingress (allowed)**:
- ✅ Only from `backend` namespace on port 5432

**Egress (allowed)**:
- ✅ To `kube-system` (DNS) on port 53
- ✅ To internet on port 443 (for backups to Cloud Storage)

## Traffic Flow Diagram

```
┌─────────┐
│ Internet│
└────┬────┘
     │
     ▼
┌────────────────┐
│ Ingress (NGINX)│
└────┬───────────┘
     │
     ▼
┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Frontend   │────▶│ Backend  │────▶│ Database │
│  (port 3000)│     │(port 8080)│     │(port 5432)│
└─────────────┘     └────┬─────┘     └──────────┘
                         │
                         ▼
                   ┌──────────────┐
                   │External APIs │
                   │  (HTTPS:443) │
                   └──────────────┘
```

## Testing Network Policies

### Test Allowed Traffic

```bash
# Frontend → Backend (should succeed)
kubectl run -it test-frontend --rm --image=busybox -n frontend -- \
  wget -O- http://backend-service.backend:8080/health

# Backend → Database (should succeed)
kubectl run -it test-backend --rm --image=busybox -n backend -- \
  nc -zv postgres-service.database 5432
```

### Test Blocked Traffic

```bash
# Frontend → Database (should fail - blocked)
kubectl run -it test-blocked --rm --image=busybox -n frontend -- \
  nc -zv postgres-service.database 5432

# Should timeout or connection refused
```

### Test DNS Resolution

```bash
# All pods should resolve DNS
kubectl run -it test-dns --rm --image=busybox -n backend -- \
  nslookup kubernetes.default
```

## Troubleshooting

### Traffic Not Working

1. **Check NetworkPolicy exists**:
   ```bash
   kubectl get netpol -n <namespace>
   kubectl describe netpol <policy-name> -n <namespace>
   ```

2. **Verify Pod Labels**:
   ```bash
   kubectl get pods -n <namespace> --show-labels
   ```
   
   Labels must match `podSelector` in NetworkPolicy.

3. **Check Namespace Labels**:
   ```bash
   kubectl get ns <namespace> --show-labels
   ```
   
   Must have `name: <namespace>` label for policies to work.

4. **Test Without Policy**:
   ```bash
   # Temporarily delete policy
   kubectl delete netpol <policy-name> -n <namespace>
   
   # Test connectivity
   # ...
   
   # Reapply
   kubectl apply -f network-policies.yaml
   ```

### DNS Not Working

Ensure DNS egress is allowed:
```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        name: kube-system
  ports:
  - protocol: UDP
    port: 53
```

## Monitoring

View network policy events:
```bash
# Check for policy violations in logs
kubectl logs -n kube-system -l k8s-app=cilium

# GKE specific
gcloud logging read "resource.type=k8s_cluster AND protoPayload.methodName:networkpolicies"
```

## Cost Impact

**Network Policies**: Free (included with Dataplane V2)

## Best Practices

✅ **Start with default-deny** then add explicit allows  
✅ **Use namespace selectors** for multi-tier apps  
✅ **Always allow DNS** (port 53 UDP to kube-system)  
✅ **Label namespaces and pods** consistently  
✅ **Test policies** before production deployment  
✅ **Document allowed flows** for troubleshooting  
✅ **Monitor policy events** for debugging

## Modifications

### Add New Service

To allow a new service to communicate:

1. **Update policy** to allow ingress/egress
2. **Add namespace selector** if cross-namespace
3. **Match pod labels** in selector
4. **Test connectivity** before production

Example - Allow monitoring to scrape metrics:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
  namespace: backend
spec:
  podSelector: {}
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080  # Metrics port
```

## Next Steps

1. Apply network policies: `kubectl apply -f network-policies.yaml`
2. Label all namespaces: `kubectl label ns <name> name=<name>`
3. Ensure pod deployments have correct labels
4. Test connectivity between services
5. Monitor for policy violations
6. Document any custom policies added

## References

- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [GKE Dataplane V2](https://cloud.google.com/kubernetes-engine/docs/concepts/dataplane-v2)
- [Network Policy Recipes](https://github.com/ahmetb/kubernetes-network-policy-recipes)
