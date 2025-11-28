output "cluster_name" {
  description = "The name of the GKE cluster"
  value       = google_container_cluster.autopilot.name
}

output "cluster_endpoint" {
  description = "The IP address of the cluster master"
  value       = google_container_cluster.autopilot.endpoint
}

output "cluster_ca_certificate" {
  description = "The public certificate that is the root of trust for the cluster"
  value       = google_container_cluster.autopilot.master_auth[0].cluster_ca_certificate
}

output "gke_sa_email" {
  description = "The email of the GKE service account"
  value       = google_service_account.gke_sa.email
}
