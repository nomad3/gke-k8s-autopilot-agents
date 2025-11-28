variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "network_id" {
  description = "VPC network ID for private IP configuration"
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL instance tier (e.g., db-f1-micro, db-g1-small, db-custom-2-7680)"
  type        = string
  default     = "db-g1-small"
}

variable "db_version" {
  description = "PostgreSQL version (e.g., POSTGRES_14, POSTGRES_15)"
  type        = string
  default     = "POSTGRES_15"
}

variable "db_storage_gb" {
  description = "Initial storage size in GB"
  type        = number
  default     = 10
}

variable "enable_ha" {
  description = "Enable high availability (REGIONAL vs ZONAL)"
  type        = bool
  default     = false
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
}
