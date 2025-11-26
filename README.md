# GKE Autopilot Migration Project

This repository contains the complete Infrastructure-as-Code (IaC) and configuration for migrating microservices from Docker Compose to **Google Kubernetes Engine (GKE) Autopilot**.

## 🚀 Project Overview

The project is structured to provide a production-ready, secure, and cost-optimized Kubernetes environment.

- **Infrastructure**: Terraform-managed GKE Autopilot, VPC, and IAM.
- **Security**: Workload Identity, Secret Manager, Network Policies, Binary Authorization.
- **Deployment**: Helm charts for microservices with Dev/Prod environment support.
- **CI/CD**: GitHub Actions pipelines for automated testing and deployment.
- **Operations**: Cloud Monitoring, Alerting, and Disaster Recovery strategies.

## 📂 Repository Structure

```
.
├── terraform/              # Infrastructure as Code (GCP resources)
│   ├── modules/            # Reusable Terraform modules
│   └── README.md           # Terraform setup guide
├── kubernetes/             # Cluster configuration manifests
│   ├── external-secrets/   # Secret management
│   ├── ingress/            # Ingress & TLS config
│   ├── network-policies/   # Security policies
│   └── namespaces/         # RBAC & Quotas
├── helm/                   # Application deployment charts
│   ├── charts/             # Generic microservice chart
│   ├── values/             # Environment-specific values (dev/prod)
│   └── README.md           # Helm usage guide
├── .github/                # CI/CD Pipelines
│   └── workflows/          # GitHub Actions definitions
├── docs/                   # Operational documentation
│   ├── backup-strategy.md
│   ├── disaster-recovery.md
│   ├── multi-environment-guide.md
│   └── production-cutover.md
└── tests/                  # Validation suite
    ├── integration/        # Connectivity tests
    └── load/               # k6 performance tests
```

## 🛠️ Prerequisites

- **Google Cloud Platform (GCP)** Account
- **Terraform** v1.5+
- **gcloud CLI**
- **kubectl**
- **Helm** v3+

## 🏁 Quick Start

### 1. Provision Infrastructure
Navigate to `terraform/` and follow the [Infrastructure Guide](terraform/README.md).
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Project ID
terraform init
terraform apply
```

### 2. Configure Cluster
Connect to your new cluster:
```bash
gcloud container clusters get-credentials gke-autopilot-cluster --region us-central1
```

### 3. Deploy Applications
Use the provided Helm charts to deploy your services. See [Helm Guide](helm/README.md).
```bash
# Deploy Backend (Dev)
helm upgrade --install backend ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -n backend --create-namespace
```

### 4. Set up CI/CD
Configure GitHub Secrets (`GCP_PROJECT_ID`, `GCP_SA_KEY`) to enable the [Automated Pipelines](.github/workflows/README.md).

## 📚 Documentation Index

- **[Infrastructure Setup](terraform/README.md)**: GKE, VPC, IAM details.
- **[Helm Charts](helm/README.md)**: Application deployment guide.
- **[Multi-Environment Guide](docs/multi-environment-guide.md)**: Dev vs Prod strategy.
- **[Backup Strategy](docs/backup-strategy.md)**: Data protection policies.
- **[Disaster Recovery](docs/disaster-recovery.md)**: Runbooks for outages.
- **[Production Cutover](docs/production-cutover.md)**: Migration checklist.

## 🔐 Security Features

- **Private Cluster**: Nodes have internal IPs only.
- **Workload Identity**: No long-lived service account keys.
- **Secret Manager**: Secrets injected at runtime via External Secrets Operator.
- **Network Policies**: Default-deny traffic between namespaces.
- **Read-Only Root Filesystem**: Enforced for containers where possible.

## 💰 Cost Optimization

- **GKE Autopilot**: Pay only for requested pod resources (CPU/RAM).
- **Spot Instances**: Configurable for Dev environments.
- **Auto-Scaling**: HPA and VPA enabled to match demand.
- **Resource Quotas**: Prevent runaway costs in namespaces.
