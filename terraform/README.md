# GKE Autopilot Terraform Configuration

Infrastructure as Code for deploying a cost-optimized Google Kubernetes Engine (GKE) Autopilot cluster with security best practices.

## Features

- **GKE Autopilot**: Fully managed Kubernetes with usage-based pricing
- **Private Cluster**: Private node IPs with Cloud NAT for egress
- **VPC-Native**: Custom VPC with secondary IP ranges for pods and services
- **Workload Identity**: Secure pod authentication without JSON keys
- **Binary Authorization**: Image security and policy enforcement
- **Managed Monitoring**: Cloud Logging and Cloud Monitoring integration
- **High Availability**: Regional cluster with multi-zone deployment

## Architecture

```
┌─────────────────────────────────────────────────┐
│              VPC Network (gke-vpc)              │
│  ┌───────────────────────────────────────────┐  │
│  │     Subnet (10.0.0.0/24)                  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │   GKE Autopilot Cluster (Regional)  │  │  │
│  │  │  - Pods: 10.1.0.0/16                │  │  │
│  │  │  - Services: 10.2.0.0/16            │  │  │
│  │  │  - Private Nodes                     │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │           │                                │  │
│  │           ▼                                │  │
│  │    Cloud NAT (egress)                      │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
           │
           ▼
    Internet / GCP Services
```

## Cost Estimate

| Component | Monthly Cost |
|-----------|-------------|
| GKE Autopilot (pod resources) | $80-130 |
| Cloud NAT | $32-50 |
| Network Egress | ~$12 |
| VPC (free) | $0 |
| **Estimated Total** | **$124-192/month** |

> **Note**: Actual costs depend on workload resource usage and network traffic.

## Prerequisites

1. **GCP Project**: Active Google Cloud project
2. **gcloud CLI**: Installed and authenticated
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Terraform**: Version >= 1.5.0
4. **Required APIs**: Enable these GCP APIs:
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable servicenetworking.googleapis.com
   gcloud services enable binaryauthorization.googleapis.com
   ```
5. **GCS Bucket**: For Terraform state (create manually):
   ```bash
   gcloud storage buckets create gs://YOUR-PROJECT-terraform-state \
     --location=US \
     --uniform-bucket-level-access
   ```

## Setup Instructions

### 1. Clone and Configure

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:
```hcl
project_id   = "your-gcp-project-id"
region       = "us-central1"
cluster_name = "gke-autopilot-cluster"
environment  = "dev"
```

### 2. Update Backend Configuration

Edit `backend.tf` and replace `YOUR-PROJECT-terraform-state` with your GCS bucket name.

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Preview Changes

```bash
terraform plan
```

### 5. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

**Deployment time**: ~10-15 minutes for GKE Autopilot cluster provisioning.

### 6. Connect to Cluster

After deployment, get kubectl credentials:
```bash
# Command is also available in Terraform outputs
terraform output -raw kubectl_connection_command | bash
```

Verify connection:
```bash
kubectl get nodes
kubectl cluster-info
```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | GCP Project ID | *required* |
| `region` | GCP region | `us-central1` |
| `cluster_name` | Cluster name | `gke-autopilot-cluster` |
| `environment` | Environment (dev/staging/prod) | `dev` |
| `enable_binary_authorization` | Enable image security | `true` |
| `enable_workload_identity` | Enable Workload Identity | `true` |
| `release_channel` | Update channel | `REGULAR` |

See `variables.tf` for complete list.

## Security Features

### Private Cluster
- Nodes have private IPs only
- Master accessible via authorized networks (configure in `authorized_networks` variable)
- Cloud NAT for outbound internet access

### Workload Identity
Enabled by default. To use in pods:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  annotations:
    iam.gke.io/gcp-service-account: my-app@PROJECT_ID.iam.gserviceaccount.com
```

### Binary Authorization
Enforce only signed container images can be deployed.

## Cost Optimization Tips

1. **Right-size pod resources**: Autopilot charges based on requests
   ```yaml
   resources:
     requests:
       cpu: "250m"      # Be precise
       memory: "512Mi"
   ```

2. **Enable Vertical Pod Autoscaling**: Already enabled, automatically optimizes requests

3. **Use namespaces with resource quotas**: Prevent runaway costs
   ```yaml
   apiVersion: v1
   kind: ResourceQuota
   metadata:
     name: compute-quota
   spec:
     hard:
       requests.cpu: "10"
       requests.memory: "20Gi"
   ```

4. **Delete unused resources**: Clean up test deployments regularly

5. **Monitor with Cloud Billing**: Set up budget alerts

6. **Consider Committed Use Discounts**: For production (37-55% savings)

## Outputs

After `terraform apply`, view outputs:
```bash
terraform output
```

Available outputs:
- `cluster_name`: Cluster identifier
- `cluster_endpoint`: API server endpoint
- `kubectl_connection_command`: Command to connect kubectl
- `workload_identity_pool`: Workload Identity pool name

## Updating Infrastructure

1. Modify configuration in `.tf` files
2. Preview changes: `terraform plan`
3. Apply changes: `terraform apply`

## Destroying Resources

**Warning**: This will delete the cluster and all workloads!

```bash
terraform destroy
```

## Troubleshooting

### Issue: "deletion_protection" prevents destroy

**Solution**: Set `deletion_protection = false` in `main.tf` before destroying:
```hcl
resource "google_container_cluster" "autopilot" {
  # ...
  deletion_protection = false
}
```

### Issue: Quota exceeded

**Solution**: Request quota increase in GCP Console or use a different region.

### Issue: API not enabled

**Solution**: Enable required APIs:
```bash
gcloud services enable container.googleapis.com compute.googleapis.com
```

## Next Steps

After infrastructure is deployed:

1. **Install Ingress Controller** (Task 3.1)
2. **Configure TLS Certificates** (Task 3.2)
3. **Create Namespaces and RBAC** (Task 3.3)
4. **Set up Secret Manager** (Task 2.1)
5. **Deploy Applications with Helm** (Phase 4)

## References

- [GKE Autopilot Documentation](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Binary Authorization](https://cloud.google.com/binary-authorization/docs)
