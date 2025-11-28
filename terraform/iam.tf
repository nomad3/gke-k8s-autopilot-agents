# ========================================
# IAM Bindings for Existing Service Accounts
# ========================================

# CI/CD Pipeline (GitHub Actions) SA
variable "cicd_sa_email" {
  type    = string
  default = "github-actions-sa@ai-agency-479516.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "cicd_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${var.cicd_sa_email}"
}

resource "google_project_iam_member" "cicd_gcr_writer" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${var.cicd_sa_email}"
}

resource "google_project_iam_member" "cicd_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${var.cicd_sa_email}"
}

# Backend app SA
variable "backend_sa_email" {
  type    = string
  default = "terraform-dev-sa@ai-agency-479516.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.backend_sa_email}"
}

resource "google_project_iam_member" "backend_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${var.backend_sa_email}"
}

# Frontend app SA
variable "frontend_sa_email" {
  type    = string
  default = "terraform-prod-sa@ai-agency-479516.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "frontend_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${var.frontend_sa_email}"
}

# Database app SA (if needed)
variable "database_sa_email" {
  type    = string
  default = "terraform-prod-sa@ai-agency-479516.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "database_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.database_sa_email}"
}

# Monitoring SA (optional)
variable "monitoring_sa_email" {
  type    = string
  default = "terraform-prod-sa@ai-agency-479516.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${var.monitoring_sa_email}"
}

resource "google_project_iam_member" "monitoring_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${var.monitoring_sa_email}"
}
