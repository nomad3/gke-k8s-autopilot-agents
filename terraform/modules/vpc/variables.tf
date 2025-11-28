variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "network_name" {
  description = "VPC network name"
  type        = string
}

variable "subnet_name" {
  description = "VPC subnet name"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
}

variable "pods_cidr_name" {
  description = "Secondary range name for pods"
  type        = string
}

variable "pods_cidr_range" {
  description = "CIDR range for pods"
  type        = string
}

variable "services_cidr_name" {
  description = "Secondary range name for services"
  type        = string
}

variable "services_cidr_range" {
  description = "CIDR range for services"
  type        = string
}

variable "cluster_name" {
  description = "GKE Autopilot cluster name (used for firewall tags)"
  type        = string
}
