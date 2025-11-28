# Cloud DNS Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name (e.g., example.com)"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
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
  description = "IP address of the Gateway load balancer"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Labels to apply to DNS resources"
  type        = map(string)
  default     = {}
}
