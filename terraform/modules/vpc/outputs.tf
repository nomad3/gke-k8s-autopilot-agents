output "network_name" {
  description = "The name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "network_id" {
  description = "The ID of the VPC network"
  value       = google_compute_network.vpc.id
}

output "subnet_name" {
  description = "The name of the subnet"
  value       = google_compute_subnetwork.subnet.name
}

output "subnet_id" {
  description = "The ID of the subnet"
  value       = google_compute_subnetwork.subnet.id
}

output "pods_range_name" {
  description = "The name of the secondary range for pods"
  value       = var.pods_cidr_name
}

output "services_range_name" {
  description = "The name of the secondary range for services"
  value       = var.services_cidr_name
}
