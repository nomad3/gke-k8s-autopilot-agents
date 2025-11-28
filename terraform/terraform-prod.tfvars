# Production Terraform Variables
# Copy to terraform-prod.tfvars and update with production values

project_id   = "ai-agency-479516" # Update with actual prod project ID
region       = "us-central1"
cluster_name = "gke-autopilot-cluster-prod"
environment  = "prod"

# Network Configuration
network_name        = "gke-vpc-prod"
subnet_name         = "gke-subnet-prod"
subnet_cidr         = "10.10.0.0/24"
pods_cidr_range     = "10.11.0.0/16"
services_cidr_range = "10.12.0.0/16"

# Authorized Networks (add production IPs)
authorized_networks = [
  # {
  #   cidr_block   = "YOUR_OFFICE_IP/32"
  #   display_name = "Office Network"
  # }
]

# Feature Flags
enable_binary_authorization     = true
enable_vertical_pod_autoscaling = true

# Release Channel for production (more stable)
release_channel = "REGULAR" # or "STABLE" for maximum stability

# Labels
labels = {
  managed_by  = "terraform"
  project     = "gke-migration"
  environment = "prod"
}

# DNS Configuration
enable_dns  = false # Set to true when you have a domain configured
domain_name = ""    # Replace with your actual domain when enabling DNS
gateway_ip  = ""    # Leave empty to fetch automatically from Gateway

# DNS Records - configure subdomains for your services
dns_records = []
# Uncomment and configure when enable_dns = true:
# dns_records = [
#   {
#     name = "api"
#     ttl  = 300
#   },
#   {
#     name = "www"
#     ttl  = 300
#   }
# ]
