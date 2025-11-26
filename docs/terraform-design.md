# Terraform Implementation Design

This document details the technical implementation of the Infrastructure-as-Code (IaC) for the GKE Autopilot migration.

## 1. Module Structure & Purpose

The project uses a **Root Module Architecture** (flat structure) to minimize complexity for a single-cluster deployment. Resources are logically grouped by file.

| File | Purpose | Key Resources |
| :--- | :--- | :--- |
| `main.tf` | Core Network & Cluster | VPC, Subnets, Cloud NAT, GKE Autopilot Cluster |
| `iam.tf` | Identity & Access | Service Accounts, Workload Identity Bindings, IAM Roles |
| `secrets.tf` | Secret Management | Secret Manager Secrets, Replication Policies |
| `registry.tf` | Artifact Management | Artifact Registry Repositories, Cleanup Policies |
| `monitoring.tf` | Observability | Alert Policies, Notification Channels |
| `backend.tf` | State Management | GCS Backend Configuration |
| `variables.tf` | Configuration | Input variable definitions and defaults |
| `outputs.tf` | Data Exports | Cluster Endpoint, CA Certificate, Service Account Emails |

## 2. Resource Management

### A. Network & Cluster (`main.tf`)
- **VPC Network**: Custom mode (`google_compute_network`)
- **Subnets**: Private nodes, Pod ranges, Service ranges (`google_compute_subnetwork`)
- **Cloud NAT**: For private node internet access (`google_compute_router`, `google_compute_router_nat`)
- **GKE Cluster**: Autopilot mode, Regional, Private Endpoint (`google_container_cluster`)

### B. Identity (`iam.tf`)
- **CI/CD SA**: For GitHub Actions (`google_service_account`)
- **Workload SAs**: Backend, Frontend, Database (`google_service_account`)
- **IAM Bindings**: Least privilege access (`google_project_iam_member`)
- **Workload Identity**: K8s SA to GCP SA mapping (`google_service_account_iam_binding`)

### C. Secrets (`secrets.tf`)
- **Secrets**: Database creds, API keys, TLS certs (`google_secret_manager_secret`)
- **Versions**: Secret payloads (`google_secret_manager_secret_version`)
- **Access**: IAM bindings for Workload Identity (`google_secret_manager_secret_iam_member`)

## 3. Order of Deployment & Dependencies

Terraform handles dependencies automatically, but the logical flow is:

1.  **Network Layer**: VPC -> Subnets -> NAT
2.  **Cluster Layer**: GKE Cluster (depends on Subnets)
3.  **Identity Layer**: Service Accounts -> IAM Roles
4.  **Workload Identity**: Binds K8s SAs (created by Helm later) to GCP SAs
5.  **Services Layer**: Registry, Secrets, Monitoring

## 4. Key Variables & Outputs

### Variables (`variables.tf`)
| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `project_id` | string | GCP Project ID | **Required** |
| `region` | string | GCP Region | `us-central1` |
| `cluster_name` | string | GKE Cluster Name | `gke-autopilot-cluster` |
| `network_name` | string | VPC Name | `gke-network` |

### Outputs (`outputs.tf`)
| Name | Description | Usage |
| :--- | :--- | :--- |
| `kubernetes_cluster_name` | Cluster Name | CI/CD |
| `kubernetes_cluster_host` | API Endpoint | `kubectl` config |
| `project_id` | GCP Project ID | CI/CD |
| `backend_sa_email` | Backend GCP SA | Helm Values |

## 5. Migration Steps

1.  **Initialize**: `terraform init` (Configures GCS backend)
2.  **Configure**: Create `terraform.tfvars` from example.
3.  **Plan**: `terraform plan -out=tfplan` (Review changes)
4.  **Apply**: `terraform apply tfplan` (Provision infra)
5.  **Connect**: `gcloud container clusters get-credentials ...`
6.  **Deploy**: Proceed to Helm chart deployment.
