output "cluster_name" {
  description = "GKE Cluster Name"
  value       = module.gke.cluster_name
}

output "workload_identity_pool" {
  description = "Workload Identity pool name"
  value       = module.gke.workload_identity_pool
}

# DNS Outputs
output "dns_zone_name" {
  description = "Name of the DNS managed zone"
  value       = var.enable_dns ? module.dns[0].zone_name : null
}

output "dns_name_servers" {
  description = "Name servers for the DNS zone (update these in your domain registrar)"
  value       = var.enable_dns ? module.dns[0].name_servers : null
}

output "dns_records" {
  description = "Created DNS records"
  value       = var.enable_dns ? module.dns[0].dns_records : null
}

output "cluster_endpoint" {
  description = "GKE Cluster Endpoint"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE Cluster CA Certificate"
  value       = module.gke.cluster_ca_certificate
  sensitive   = true
}

output "vpc_network_name" {
  description = "VPC Network Name"
  value       = module.vpc.network_name
}

output "vpc_subnet_name" {
  description = "VPC Subnet Name"
  value       = module.vpc.subnet_name
}
