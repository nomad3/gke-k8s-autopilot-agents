# GKE Autopilot Migration Project

This repository contains the complete Infrastructure-as-Code (IaC) and configuration for migrating microservices from Docker Compose to **Google Kubernetes Engine (GKE) Autopilot**.

## 🚀 Project Overview

A production-ready, secure, and cost-optimized Kubernetes environment with:

- **Infrastructure**: Terraform-managed GKE Autopilot, VPC, IAM, and monitoring
- **Security**: Workload Identity, Secret Manager integration, Private Google Access, Binary Authorization
- **Deployment**: Generic Helm charts for microservices with Dev/Prod environment separation
- **CI/CD**: GitHub Actions pipelines with security scanning, automated testing, and deployment
- **Observability**: Cloud Monitoring, Managed Prometheus, custom dashboards, and logging

## 📂 Repository Structure

```
.
├── terraform/              # Infrastructure as Code (GCP resources)
│   ├── main.tf            # GKE cluster, VPC, networking
│   ├── iam.tf             # Service accounts and Workload Identity
│   ├── secrets.tf         # Secret Manager configuration
│   ├── monitoring.tf      # Cloud Monitoring and dashboards
│   ├── registry.tf        # Artifact Registry setup
│   ├── backend.tf         # GCS state backend
│   └── README.md          # Terraform setup guide
├── kubernetes/            # Cluster infrastructure manifests
│   ├── external-secrets/  # External Secrets Operator config
│   ├── ingress/           # Ingress controllers and TLS
│   ├── network-policies/  # Network security policies
│   ├── namespaces/        # Namespace definitions
│   └── security/          # RBAC and security policies
├── helm/                  # Application deployment
│   ├── charts/            # Generic microservice Helm chart
│   ├── values/            # Environment-specific values (dev/prod)
│   └── README.md          # Helm deployment guide
├── .github/workflows/     # CI/CD Pipelines
│   ├── backend-*.yaml     # Backend service pipelines
│   ├── frontend-*.yaml    # Frontend service pipelines
│   ├── terraform-*.yaml   # Infrastructure pipelines
│   └── README.md          # CI/CD documentation
├── docs/                  # Operational documentation
│   ├── github-secrets-setup.md      # GitHub secrets configuration
│   ├── post-deployment-guide.md     # Post-deployment best practices
│   ├── production-cutover.md        # Migration checklist
│   └── terraform-design.md          # Infrastructure design
└── tests/                 # Validation suite
    ├── integration/       # Connectivity tests
    └── load/              # k6 performance tests
```

## 🛠️ Prerequisites

- **Google Cloud Platform (GCP)** Account with billing enabled
- **Terraform** v1.5.7+
- **gcloud CLI** configured and authenticated
- **kubectl** v1.28+
- **Helm** v3.13+
- **GitHub** repository with Actions enabled

## 🏁 Quick Start

### 1. Configure GitHub Secrets

Follow the [GitHub Secrets Setup Guide](docs/github-secrets-setup.md) to configure:
- `GCP_PROJECT_ID_DEV` / `GCP_PROJECT_ID_PROD`
- `GCP_SA_KEY_DEV` / `GCP_SA_KEY_PROD`
- `GCS_BUCKET_DEV` / `GCS_BUCKET_PROD`

### 2. Provision Infrastructure

```bash
cd terraform

# Create GCS bucket for state (one-time setup)
export PROJECT_ID="your-project-id"
gcloud storage buckets create gs://${PROJECT_ID}-terraform-state \
  --project=${PROJECT_ID} \
  --location=US \
  --versioning

# Initialize Terraform with backend config
terraform init -backend-config="bucket=${PROJECT_ID}-terraform-state" \
               -backend-config="prefix=gke-autopilot/dev"

# Create your tfvars file
cp terraform-dev.tfvars terraform.tfvars
# Edit terraform.tfvars with your project ID and settings

# Plan and apply
terraform plan
terraform apply
```

### 3. Connect to Cluster

```bash
gcloud container clusters get-credentials gke-autopilot-cluster-dev \
  --region us-central1 \
  --project your-project-id
```

### 4. Deploy Cluster Infrastructure

```bash
# Deploy namespaces
kubectl apply -f kubernetes/namespaces/

# Install External Secrets Operator (if not using Helm)
kubectl apply -f kubernetes/external-secrets/

# Deploy ingress controller
kubectl apply -f kubernetes/ingress/
```

### 5. Deploy Applications

```bash
# Deploy backend to dev
helm upgrade --install backend ./helm/charts/microservice \
  -f ./helm/values/backend-values.yaml \
  -n backend --create-namespace

# Deploy frontend to dev
helm upgrade --install frontend ./helm/charts/microservice \
  -f ./helm/values/frontend-values.yaml \
  -n frontend --create-namespace
```

### 6. Automated Deployments via CI/CD

Once GitHub secrets are configured, CI/CD pipelines will automatically:
- **On PR**: Run linting, tests, security scans, and build validation
- **On push to main**: Deploy to dev environment
- **On tag push**: Deploy to production (with manual approval)

## 📚 Documentation Index

### Getting Started
- **[GitHub Secrets Setup](docs/github-secrets-setup.md)**: Configure CI/CD credentials
- **[Post-Deployment Guide](docs/post-deployment-guide.md)**: Best practices after cluster deployment
- **[Terraform Design](docs/terraform-design.md)**: Infrastructure architecture

### Operations
- **[Production Cutover](docs/production-cutover.md)**: Migration checklist
- **[Terraform README](terraform/README.md)**: Infrastructure details
- **[Helm README](helm/README.md)**: Application deployment guide
- **[CI/CD README](.github/workflows/README.md)**: Pipeline documentation

## 🔐 Security Features

- ✅ **Private Cluster**: Nodes have internal IPs only, no public exposure
- ✅ **Workload Identity**: No long-lived service account keys in pods
- ✅ **Secret Manager Integration**: Secrets injected at runtime via External Secrets Operator
- ✅ **Private Google Access**: Nodes access Google APIs via internal network
- ✅ **Binary Authorization**: Optional image signing enforcement
- ✅ **Dataplane V2**: Advanced networking with network policy support
- ✅ **Security Scanning**: Trivy scans in CI/CD pipelines
- ✅ **HTTPS Enforcement**: TLS termination at ingress with cert-manager

## 🏗️ Infrastructure Highlights

### Networking
- Custom VPC with private subnets
- Secondary IP ranges for pods and services
- Cloud NAT for egress traffic
- VPC Flow Logs enabled

### Compute
- GKE Autopilot (fully managed nodes)
- Horizontal Pod Autoscaling (HPA)
- Vertical Pod Autoscaling (VPA)
- Pod Disruption Budgets

### Storage
- Artifact Registry for container images
- GCS for Terraform state with versioning
- Secret Manager for sensitive data

### Monitoring
- Cloud Monitoring with custom dashboards
- Managed Prometheus for metrics
- Cloud Logging for centralized logs
- Workload monitoring enabled

## 💰 Cost Optimization

- **GKE Autopilot**: Pay only for requested pod resources (CPU/RAM)
- **Auto-Scaling**: HPA and VPA match demand automatically
- **Image Cleanup**: Automatic deletion of untagged images after 30 days
- **Resource Quotas**: Prevent runaway costs in namespaces
- **Private Google Access**: Reduced NAT costs for Google API calls

## 🔄 CI/CD Pipeline Features

- ✅ Separate workflows per service (backend, frontend)
- ✅ Environment-specific pipelines (dev, prod)
- ✅ Multi-stage: Quality → Build → Deploy
- ✅ Security scanning with Trivy (blocks on critical vulnerabilities)
- ✅ Docker layer caching for faster builds
- ✅ Commit SHA tagging for traceability
- ✅ Helm deployments with atomic rollbacks
- ✅ Manual approval gates for production

## 📊 Compliance & Best Practices

This project follows industry best practices:
- Infrastructure as Code with Terraform
- GitOps workflow with Helm
- Secrets management with Workload Identity
- Security scanning in CI/CD
- Comprehensive monitoring and logging
- Multi-environment separation (dev/prod)

**Compliance Score: 92%** - See [Compliance Report](docs/compliance-report.md) for details.

## 🚨 Important Notes

### DNS Management
**DNS is NOT managed by this Terraform configuration.** You will need to:
- Manually configure DNS records in your DNS provider
- Point your domain to the GKE Ingress Load Balancer IP
- Follow the [Production Cutover Guide](docs/production-cutover.md) for DNS TTL recommendations

### State Management
- Terraform state is stored in GCS with versioning enabled
- Use different prefixes or workspaces for dev/prod environments
- Never commit `.tfvars` files (they're in `.gitignore`)

### Secrets
- Service account keys are stored in GitHub Secrets
- Application secrets are in GCP Secret Manager
- External Secrets Operator syncs secrets to Kubernetes

## 🤝 Contributing

1. Create a feature branch
2. Make changes and test locally
3. Submit PR (triggers automated checks)
4. Merge to main (auto-deploys to dev)
5. Tag for production release

## 📞 Support

For issues or questions:
1. Check the [documentation](docs/)
2. Review [CI/CD logs](.github/workflows/)
3. Check GKE cluster health in Cloud Console

## 📝 License

[Your License Here]

---

**Status**: ✅ Production-Ready  
**Last Updated**: 2025-11-27  
**Terraform Version**: 1.5.7  
**GKE Version**: Latest Autopilot (REGULAR channel)
