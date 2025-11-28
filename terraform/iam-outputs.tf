# Additional Terraform Outputs for IAM

output "cicd_service_account_email" {
  description = "CI/CD pipeline service account email"
  value       = data.google_service_account.cicd_sa.email
}

output "backend_app_service_account_email" {
  description = "Backend application service account email"
  value       = data.google_service_account.backend_app_sa.email
}

output "frontend_app_service_account_email" {
  description = "Frontend application service account email"
  value       = data.google_service_account.frontend_app_sa.email
}

output "database_app_service_account_email" {
  description = "Database application service account email"
  value       = data.google_service_account.database_app_sa.email
}

output "backup_service_account_email" {
  description = "Backup and restore service account email"
  value       = data.google_service_account.backup_sa.email
}

output "monitoring_service_account_email" {
  description = "Monitoring service account email"
  value       = data.google_service_account.monitoring_sa.email
}
