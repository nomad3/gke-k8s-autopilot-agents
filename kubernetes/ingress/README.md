# Ingress Controller Configuration

This directory contains configuration for the NGINX Ingress Controller, TLS certificates, and example Ingress resources.

## Overview

The NGINX Ingress Controller manages external access to services in the cluster, providing:
- HTTP/HTTPS load balancing
- SSL/TLS termination
- Path-based routing
- Rate limiting and security headers

## Files

- `nginx-values.yaml` - Helm chart values for NGINX Ingress Controller
- `certificates.yaml` - TLS certificate configuration (Google-managed or cert-manager)
- `ingress-examples.yaml` - Example Ingress resources for frontend and backend

## Installation

### 1. Create Namespace

```bash
kubectl create namespace ingress-nginx
kubectl label namespace ingress-nginx name=ingress-nginx
```

### 2. Add Helm Repository

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

### 3. Install NGINX Ingress Controller

```bash
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx \
  -f nginx-values.yaml \
  --wait
```

**Deployment time**: ~3-5 minutes

### 4. Verify Installation

```bash
# Check pods
kubectl get pods -n ingress-nginx

# Check service (get external IP)
kubectl get svc -n ingress-nginx

# Check ingress class
kubectl get ingressclass
```

### 5. Get Load Balancer IP

```bash
kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Update your DNS records to point to this IP address.

## TLS Certificate Management

### Option 1: Google-Managed Certificates (Recommended)

**Pros**: Automatic provisioning and renewal, free, no maintenance

1. Edit `certificates.yaml` with your domains
2. Apply: `kubectl apply -f certificates.yaml`
3. Add annotation to Ingress:
   ```yaml
   metadata:
     annotations:
       networking.gke.io/managed-certificates: "app-managed-cert"
   ```

**Provisioning time**: 15-60 minutes

### Option 2: cert-manager with Let's Encrypt

**Pros**: More control, works with any cloud provider

1. Install cert-manager:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

2. Uncomment cert-manager configuration in `certificates.yaml`
3. Update email address in ClusterIssuer
4. Apply: `kubectl apply -f certificates.yaml`
5. Add annotation to Ingress:
   ```yaml
   metadata:
     annotations:
       cert-manager.io/cluster-issuer: "letsencrypt-prod"
   ```

## Creating Ingress Resources

### Basic Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  namespace: frontend
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - example.com
    secretName: app-tls-secret
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Apply Ingress

```bash
# Update domains and service names in ingress-examples.yaml
kubectl apply -f ingress-examples.yaml
```

## Features Configured

### ✅ High Availability
- 2 replicas minimum
- Horizontal Pod Autoscaling (2-5 replicas)
- Pod Disruption Budget

### ✅ Security
- Non-root user
- Read-only root filesystem
- Dropped capabilities (except NET_BIND_SERVICE)
- HSTS headers
- TLS 1.2+ only
- Security headers (X-Frame-Options, etc.)

### ✅ Performance
- 2 worker processes
- 16,384 max connections
- Gzip compression
- Connection pooling

### ✅ Monitoring
- Prometheus metrics enabled
- ServiceMonitor for Prometheus Operator

### ✅ Cost Optimization
- Resource requests: 100m CPU, 128Mi memory
- Autoscaling based on CPU/memory
- Single external Load Balancer for all apps

## Cost Impact

| Component | Monthly Cost |
|-----------|-------------|
| External Load Balancer | ~$18 |
| Ingress pods (Autopilot) | ~$5-10 |
| **Total** | **~$23-28** |

## Testing

### Test HTTP Access

```bash
# Get LB IP
LB_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test with curl (replace example.com with your domain)
curl -H "Host: example.com" http://$LB_IP

# Test HTTPS redirect
curl -I -H "Host: example.com" http://$LB_IP
# Should return 308 Permanent Redirect to HTTPS
```

### Test TLS Certificate

```bash
# Check certificate
echo | openssl s_client -servername example.com -connect $LB_IP:443 2>/dev/null | openssl x509 -noout -text

# Or use curl
curl -v https://example.com
```

## Troubleshooting

### Ingress Not Working

```bash
# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Check ingress resource
kubectl describe ingress <ingress-name> -n <namespace>

# Check service exists
kubectl get svc <service-name> -n <namespace>
```

### TLS Certificate Not Provisioning

**Google-managed**:
```bash
# Check ManagedCertificate status
kubectl describe managedcertificate app-managed-cert

# Common issues:
# - DNS not pointing to Load Balancer IP
# - Takes 15-60 minutes to provision
# - Check domain validation
```

**cert-manager**:
```bash
# Check certificate status
kubectl describe certificate <cert-name> -n <namespace>

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```

### 404 Not Found

- Verify service name and port match Ingress backend
- Check service endpoints: `kubectl get endpoints <service-name> -n <namespace>`
- Verify pod labels match service selector

## Security Best Practices

✅ **Always use TLS** for production  
✅ **Enable HSTS** headers  
✅ **Set rate limits** to prevent abuse  
✅ **Use security headers** (X-Frame-Options, CSP)  
✅ **Restrict CORS** to known origins  
✅ **Monitor access logs** for suspicious activity  
✅ **Keep NGINX updated** via Helm chart upgrades

## Maintenance

### Upgrade Ingress Controller

```bash
# Update Helm repo
helm repo update

# Check for updates
helm search repo ingress-nginx

# Upgrade
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx \
  -f nginx-values.yaml
```

### Monitor Performance

```bash
# Check metrics
kubectl top pods -n ingress-nginx

# View Prometheus metrics
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller-metrics 10254:10254
curl http://localhost:10254/metrics
```

## Next Steps

1. ✅ Install NGINX Ingress Controller
2. ✅ Configure TLS certificates
3. Create Ingress resources for your applications
4. Point DNS to Load Balancer IP
5. Test HTTP → HTTPS redirect
6. Verify TLS certificate
7. Set up monitoring dashboards

## References

- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [GKE Ingress](https://cloud.google.com/kubernetes-engine/docs/concepts/ingress)
- [Google-managed Certificates](https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs)
- [cert-manager](https://cert-manager.io/)
