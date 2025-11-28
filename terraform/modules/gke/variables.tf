variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "cluster_name" {
  description = "GKE Autopilot cluster name"
  type        = string
}

variable "network_id" {
  description = "The ID of the VPC network"
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet"
  type        = string
}

variable "pods_range_name" {
  description = "The name of the secondary range for pods"
  type        = string
}

variable "services_range_name" {
  description = "The name of the secondary range for services"
  type        = string
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for GKE master nodes (private cluster)"
  type        = string
}

variable "authorized_networks" {
  description = "List of authorized networks for cluster API access"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
}

variable "enable_binary_authorization" {
  description = "Enable Binary Authorization for image security"
  type        = bool
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable Vertical Pod Autoscaling"
  type        = bool
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}
