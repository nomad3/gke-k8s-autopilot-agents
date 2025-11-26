# Helm Charts for GKE Autopilot Migration

This directory contains Helm charts for deploying microservices to Google Kubernetes Engine (Autopilot).

## Structure

```
helm/
├── charts/
│   └── microservice/          # Generic reusable chart
│       ├── Chart.yaml
│       ├── values.yaml                # Default values
│       └── templates/          # Kubernetes resource templates
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── serviceaccount.yaml
│           ├── configmap.yaml
│           ├── externalsecret.yaml
│           ├── pvc.yaml
│           ├── hpa.yaml
│           ├── ingress.yaml
│           └── pdb.yaml
└── values/
    ├── backend-values.yaml    # Backend API overrides
    ├── frontend-values.yaml   # Frontend app overrides
    └── database-values.yaml   # Database overrides
```

## Generic Microservice Chart

The `microservice` chart is a reusable template that can be customized for any service via values files.

### Features

✅ **Security Hardening**:
- Pod Security Standards compliant (restricted)
- Non-root user execution
- Read-only root filesystem
- Dropped capabilities
- Seccomp profile

✅ **Cost Optimization**:
- Precise resource requests and limits
- Horizontal Pod Autoscaling
- Efficient resource allocation for Autopilot billing

✅ **High Availability**:
- Multiple replicas
- Pod Disruption Budget
- Health probes (liveness, readiness)

✅ **Secret Management**:
- ExternalSecret integration with Google Secret Manager
- ConfigMap for non-sensitive data
- No secrets in Git

✅ **Observability**:
- Prometheus-compatible metrics
- Pod metadata environment variables
- ConfigMap checksum for automatic restarts

✅ **Storage**:
- PersistentVolumeClaim support
- Temporary volumes for read-only filesystem
- GKE Persistent Disk integration

## Quick Start

### 1. Update Values Files

Edit the service-specific values files in `helm/values/`:

```bash
# Update PROJECT_ID in all values files
sed -i 's/PROJECT_ID/your-gcp-project-id/g' helm/values/*.yaml

# Update domains
sed -i 's/example.com/yourdomain.com/g' helm/values/*.yaml
```

### 2. Deploy Backend Service

```bash
helm upgrade --install backend \
  ./charts/microservice \
  -f ./values/backend-values.yaml \
  -n backend \
  --create-namespace
```

### 3. Deploy Frontend Service

```bash
helm upgrade --install frontend \
  ./charts/microservice \
  -f ./values/frontend-values.yaml \
  -n frontend \
  --create-namespace
```

### 4. Deploy Database

```bash
helm upgrade --install postgres \
  ./charts/microservice \
  -f ./values/database-values.yaml \
  -n database \
  --create-namespace
```

## Customization

### Override Values

Create environment-specific values files:

```yaml
# values/backend-prod.yaml
environment: prod
replicaCount: 3
autoscaling:
  minReplicas: 3
  maxReplicas: 20
resources:
  requests:
    cpu: 500m
    memory: 1Gi
```

Deploy with overrides:
```bash
helm upgrade --install backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  -f ./values/backend-prod.yaml \
  -n backend
```

### Template Customization

For service-specific needs, create a dedicated chart:

```bash
# Copy base chart
cp -r charts/microservice charts/my-service

# Customize templates
# Edit charts/my-service/templates/*.yaml
```

## Configuration Guide

### Resource Requests

**Critical for Autopilot billing**: Autopilot charges based on resource requests.

```yaml
resources:
  requests:
    cpu: 250m      # Billed amount
    memory: 512Mi  # Billed amount
  limits:
    cpu: 500m      # Max allowed
    memory: 1Gi    # Max allowed
```

**Best practices**:
- Set requests to actual usage (not over-provision)
- Use VPA recommendations
- Monitor actual usage and adjust

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2        # HA minimum
  maxReplicas: 10       # Cost control
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Secrets from Secret Manager

```yaml
secret:
  enabled: true
  externalSecret:
    enabled: true
    secretStoreName: gcpsm-secret-store
    refreshInterval: 1h
    data:
      - secretKey: DATABASE_PASSWORD
        remoteRef:
          key: dev-database-password
```

### Persistent Storage

```yaml
persistence:
  enabled: true
  accessMode: ReadWriteOnce
  size: 50Gi
  storageClass: "standard-rwo"  # SSD: premium-rwo
  mountPath: /data
```

**Storage Classes**:
- `standard-rwo` - Standard persistent disk (HDD)
- `premium-rwo` - SSD persistent disk (faster, more expensive)

### Ingress

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.example.com
      paths:
        - path: /api
          pathType: Prefix
  tls:
    - secretName: api-tls-secret
      hosts:
        - api.example.com
```

## Deployment Workflow

### Development

```bash
# 1. Template to see generated YAML
helm template backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  > /tmp/backend-rendered.yaml

# 2. Validate
kubectl apply --dry-run=client -f /tmp/backend-rendered.yaml

# 3. Deploy to dev
helm upgrade --install backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  -n backend --create-namespace
```

### Staging/Production

```bash
# Use specific values file
helm upgrade --install backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  -f ./values/backend-prod.yaml \
  -n backend

# Or set values via CLI
helm upgrade --install backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  --set image.tag=v1.2.3 \
  --set replicaCount=5 \
  -n backend
```

## Helm Commands

### Install/Upgrade

```bash
helm upgrade --install <release-name> <chart-path> \
  -f <values-file> \
  -n <namespace>
```

### List Releases

```bash
helm list -A
helm list -n backend
```

### Get Values

```bash
# Show computed values
helm get values backend -n backend

# Show all values (with defaults)
helm get values backend -n backend --all
```

### Rollback

```bash
# Show release history
helm history backend -n backend

# Rollback to previous version
helm rollback backend -n backend

# Rollback to specific revision
helm rollback backend 3 -n backend
```

### Uninstall

```bash
helm uninstall backend -n backend
```

## Troubleshooting

### Helm Template Errors

```bash
# Lint the chart
helm lint ./charts/microservice -f ./values/backend-values.yaml

# Render templates to see output
helm template backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  --debug
```

### Resource Not Created

```bash
# Check Helm release status
helm status backend -n backend

# View release manifest
helm get manifest backend -n backend

# Check for errors in pod
kubectl describe pod <pod-name> -n backend
kubectl logs <pod-name> -n backend
```

### Values Not Applied

```bash
# Verify current values
helm get values backend -n backend --all

# Force upgrade
helm upgrade backend ./charts/microservice \
  -f ./values/backend-values.yaml \
  --force \
  -n backend
```

## Best Practices

✅ **Version Control**: Commit Helm charts and values to Git  
✅ **Values Files**: Separate values per environment (dev, staging, prod)  
✅ **Secrets**: Never commit secrets in values files  
✅ **Resource Limits**: Always set requests and limits  
✅ **Health Probes**: Configure liveness and readiness probes  
✅ **Labels**: Use consistent labels for monitoring and selection  
✅ **Namespace**: Deploy to appropriate namespaces  
✅ **Rollbacks**: Test rollback procedures  
✅ **Documentation**: Document custom values and configurations

## Migration from Docker Compose

| Docker Compose | Helm Chart |
|----------------|------------|
| `services` | Deployment + Service |
| `environment` | ConfigMap + Secret/ExternalSecret |
| `volumes` | PersistentVolumeClaim |
| `ports` | Service.port |
| `depends_on` | Init containers or readiness probes |
| `restart` | Deployment (automatic) |
| `networks` | Kubernetes networking (automatic) |

## Cost Estimation

**Example Backend Service**:
- Requests: 250m CPU, 512Mi RAM
- Replicas: 2-10 (average 4)
- **Cost**: ~$15-30/month for pods

**Example Frontend Service**:
- Requests: 100m CPU, 256Mi RAM
- Replicas: 2-8 (average 3)
- **Cost**: ~$5-15/month for pods

**Database**:
- Requests: 500m CPU, 1Gi RAM
- Replicas: 1
- Storage: 50Gi SSD
- **Cost**: ~$20-25/month (pod + storage)

**Total Application Stack**: ~$40-70/month (excluding infrastructure costs)

## Next Steps

1. ✅ Customize values files for your services
2. Deploy to dev namespace first
3. Test functionality and connections
4. Verify External Secrets synchronization
5. Check resource usage and adjust requests
6. Configure monitoring and alerts
7. Deploy to staging/production
8. Set up CI/CD pipeline for automated deployments

## References

- [Helm Documentation](https://helm.sh/docs/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [GKE Autopilot](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview) 
- [Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
