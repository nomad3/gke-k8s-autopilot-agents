# Terraform Variables for GKE Autopilot Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE Autopilot cluster name"
  type        = string
  default     = "gke-autopilot-cluster"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Network Configuration
variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "gke-vpc"
}

variable "subnet_name" {
  description = "VPC subnet name"
  type        = string
  default     = "gke-subnet"
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "pods_cidr_name" {
  description = "Secondary range name for pods"
  type        = string
  default     = "pods"
}

variable "pods_cidr_range" {
  description = "CIDR range for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr_name" {
  description = "Secondary range name for services"
  type        = string
  default     = "services"
}

variable "services_cidr_range" {
  description = "CIDR range for services"
  type        = string
  default     = "10.2.0.0/16"
}

# Cluster Configuration
variable "master_ipv4_cidr_block" {
  description = "CIDR block for GKE master nodes (private cluster)"
  type        = string
  default     = "172.16.0.0/28"
}

variable "authorized_networks" {
  description = "List of authorized networks for cluster API access"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = [
    # Add your IP ranges here, e.g.:
    # {
    #   cidr_block   = "203.0.113.0/24"
    #   display_name = "Office Network"
    # }
  ]
}

variable "enable_binary_authorization" {
  description = "Enable Binary Authorization for image security"
  type        = bool
  default     = true
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable Vertical Pod Autoscaling"
  type        = bool
  default     = true
}

# Labels and Tags
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    managed_by = "terraform"
    project    = "gke-migration"
  }
}

# DNS Configuration
variable "enable_dns" {
  description = "Enable Cloud DNS management"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Primary domain name for DNS management (e.g., example.com)"
  type        = string
  default     = ""
}

variable "dns_records" {
  description = "List of DNS A records to create"
  type = list(object({
    name = string
    ttl  = number
  }))
  default = []
}

variable "gateway_ip" {
  description = "IP address of the Gateway load balancer (leave empty to fetch automatically)"
  type        = string
  default     = ""
}


variable "enable_agentprovision_worker" {
  description = "Enable AgentProvision Worker Workload Identity"
  type        = bool
  default     = false
}
